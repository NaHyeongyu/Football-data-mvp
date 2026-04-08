"use client";

import type { FormEvent, KeyboardEvent } from "react";
import { useEffect, useRef, useState } from "react";

import type {
  AssistantQueryResponse,
  AssistantQueryStep,
} from "@/lib/team-api-types";

type MessageRole = "assistant" | "system" | "user";

type ChatMessage = {
  id: string;
  role: MessageRole;
  content: string;
  response?: AssistantQueryResponse;
};

const INITIAL_MESSAGE: ChatMessage = {
  id: "assistant-welcome",
  role: "assistant",
  content:
    "무엇을 도와드릴까요?\n경기, 훈련, 부상, 평가, 상담 데이터를 자연어 한 번으로 묶어서 조회할 수 있습니다.\n각 질문은 독립적으로 실행되며, DB 조회 결과와 모델 응답을 함께 정리합니다.",
};

function createId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function extractErrorMessage(payload: unknown, fallback: string) {
  if (payload && typeof payload === "object") {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
  }

  return fallback;
}

function formatPreviewValue(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function getPreviewKeys(step: AssistantQueryStep) {
  const firstRow = step.preview[0];
  return firstRow ? Object.keys(firstRow).slice(0, 6) : [];
}

function messageLabel(role: MessageRole) {
  if (role === "user") {
    return "You";
  }
  if (role === "system") {
    return "System";
  }
  return "Assistant";
}

function messageAvatar(role: MessageRole) {
  if (role === "user") {
    return "U";
  }
  if (role === "system") {
    return "!";
  }
  return "A";
}

function MessageTrace({ response }: { response: AssistantQueryResponse }) {
  return (
    <details className="assistant-trace">
      <summary className="assistant-trace__summary">
        <div>
          <strong>실행 로그</strong>
          <span>
            {response.provider} · {response.model} · Step {response.steps.length}
          </span>
        </div>
        <span className="assistant-trace__toggle">열기</span>
      </summary>

      <div className="assistant-trace__body">
        {response.steps.map((step) => {
          const previewKeys = getPreviewKeys(step);

          return (
            <article className="assistant-step-card" key={`${step.step}-${step.action}`}>
              <div className="assistant-step-card__head">
                <strong>
                  Step {step.step} · {step.action.toUpperCase()}
                </strong>
                {step.row_count !== null ? <span>{step.row_count} rows</span> : null}
              </div>

              {step.reason ? (
                <p className="assistant-step-card__reason">{step.reason}</p>
              ) : null}

              {step.error ? (
                <p className="assistant-step-card__error">{step.error}</p>
              ) : null}

              {step.sql ? (
                <pre className="assistant-code-block">{step.sql}</pre>
              ) : null}

              {previewKeys.length > 0 ? (
                <div className="assistant-preview-wrap">
                  <table className="assistant-preview-table">
                    <thead>
                      <tr>
                        {previewKeys.map((key) => (
                          <th key={key}>{key}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {step.preview.map((row, rowIndex) => (
                        <tr key={`${step.step}-${rowIndex}`}>
                          {previewKeys.map((key) => (
                            <td key={`${rowIndex}-${key}`}>{formatPreviewValue(row[key])}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </article>
          );
        })}
      </div>
    </details>
  );
}

export function AssistantWorkspace() {
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_MESSAGE]);
  const [draft, setDraft] = useState("");
  const [requestError, setRequestError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [isSubmitting, messages]);

  async function submitQuestion(question: string) {
    const normalizedQuestion = question.trim();
    if (!normalizedQuestion || isSubmitting) {
      return;
    }

    const userMessageId = createId();

    setRequestError(null);
    setIsSubmitting(true);
    setMessages((current) => [
      ...current,
      {
        id: userMessageId,
        role: "user",
        content: normalizedQuestion,
      },
    ]);

    try {
      const response = await fetch("/api/assistant/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: normalizedQuestion }),
      });
      const payload = (await response.json().catch(() => null)) as
        | AssistantQueryResponse
        | { detail?: string }
        | null;

      if (!response.ok) {
        throw new Error(
          extractErrorMessage(
            payload,
            `Assistant query failed (${response.status})`,
          ),
        );
      }

      const result = payload as AssistantQueryResponse;
      setMessages((current) => [
        ...current,
        {
          id: createId(),
          role: "assistant",
          content: result.answer,
          response: result,
        },
      ]);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "질의 처리 중 오류가 발생했습니다.";

      setRequestError(message);
      setMessages((current) => [
        ...current,
        {
          id: createId(),
          role: "system",
          content: `응답을 가져오지 못했습니다. ${message}`,
        },
      ]);
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextQuestion = draft;
    if (!nextQuestion.trim() || isSubmitting) {
      return;
    }

    setDraft("");
    void submitQuestion(nextQuestion);
  }

  function handleTextareaKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter" || event.shiftKey) {
      return;
    }

    event.preventDefault();
    if (!draft.trim() || isSubmitting) {
      return;
    }

    const nextQuestion = draft;
    setDraft("");
    void submitQuestion(nextQuestion);
  }

  return (
    <section className="assistant-shell">
      <section className="assistant-stage">
        <div className="assistant-thread">
          <div className="assistant-message-stack">
            {messages.map((message) => (
              <div
                className={
                  message.role === "user"
                    ? "assistant-bubble-row assistant-bubble-row--user"
                    : "assistant-bubble-row"
                }
                id={message.id}
                key={message.id}
              >
                {message.role !== "user" ? (
                  <span className={`assistant-bubble__avatar assistant-bubble__avatar--${message.role}`}>
                    {messageAvatar(message.role)}
                  </span>
                ) : null}

                <article
                  className={`assistant-bubble assistant-bubble--${message.role}`}
                >
                  <div className="assistant-bubble__meta">
                    <strong>{messageLabel(message.role)}</strong>
                    {message.response ? (
                      <span>
                        {message.response.provider} · {message.response.model}
                      </span>
                    ) : null}
                  </div>

                  <div className="assistant-bubble__body">{message.content}</div>

                  {message.response ? <MessageTrace response={message.response} /> : null}
                </article>

                {message.role === "user" ? (
                  <span className="assistant-bubble__avatar assistant-bubble__avatar--user">
                    {messageAvatar(message.role)}
                  </span>
                ) : null}
              </div>
            ))}

            {isSubmitting ? (
              <div className="assistant-bubble-row">
                <span className="assistant-bubble__avatar assistant-bubble__avatar--assistant">
                  A
                </span>
                <article className="assistant-bubble assistant-bubble--assistant assistant-bubble--pending">
                  <div className="assistant-bubble__meta">
                    <strong>Assistant</strong>
                    <span>질의 실행 중</span>
                  </div>
                  <div className="assistant-bubble__body">
                    데이터 조회와 응답 생성을 진행하고 있습니다.
                  </div>
                </article>
              </div>
            ) : null}

            <div ref={messagesEndRef} />
          </div>
        </div>

        <form className="assistant-service-composer" onSubmit={handleSubmit}>
          <div className="assistant-service-composer__surface">
            <label className="assistant-service-composer__field">
              <textarea
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={handleTextareaKeyDown}
                placeholder="예: 최근 2주간 활동량이 높았지만 부상 위험도도 높은 선수 알려줘."
                ref={textareaRef}
                rows={4}
                value={draft}
              />
            </label>

            <div className="assistant-service-composer__footer">
              <div className="assistant-service-composer__meta">
                <span>`Enter` 전송</span>
                <span>`Shift + Enter` 줄바꿈</span>
              </div>

              <button
                className="primary-button assistant-service-composer__submit"
                disabled={!draft.trim() || isSubmitting}
                type="submit"
              >
                {isSubmitting ? "질의 중..." : "보내기"}
              </button>
            </div>
          </div>

          {requestError ? (
            <p className="assistant-service-composer__error">{requestError}</p>
          ) : null}
        </form>
      </section>
    </section>
  );
}
