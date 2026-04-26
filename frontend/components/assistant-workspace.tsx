"use client";

import type { FormEvent, KeyboardEvent } from "react";
import { useEffect, useRef, useState } from "react";

import type {
  AssistantQueryResponse,
  AssistantQueryStep,
  AssistantStatusResponse,
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
    "질문을 입력하면 정형 DB 조회와 pgvector RAG 검색을 함께 실행합니다. 선수, 경기, 훈련, 부상, 평가, 상담 데이터를 함께 물어볼 수 있습니다.",
};

const SAMPLE_QUESTIONS = [
  "최근 2주 훈련 부하가 높은 선수 알려줘",
  "부상 위험도 높은 선수와 이유 알려줘",
  "최근 경기 폼 좋은 선수 추천해줘",
  "오재민 최근 평가랑 상담 내용 종합해줘",
];

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

function MessageTrace({ response }: { response: AssistantQueryResponse }) {
  return (
    <details className="assistant-trace">
      <summary className="assistant-trace__summary">
        <div>
          <strong>실행 로그</strong>
          <span>
            {response.provider} · {response.model} · {response.steps.length} steps
          </span>
        </div>
        <span className="assistant-trace__toggle">열기</span>
      </summary>

      <div className="assistant-trace__body">
        {response.steps.map((step) => {
          const previewKeys = getPreviewKeys(step);

          return (
            <article className="assistant-step-card" key={`${step.step}-${step.action}-${step.tool ?? "none"}`}>
              <div className="assistant-step-card__head">
                <strong>
                  Step {step.step} · {step.tool ?? step.action}
                </strong>
                {step.row_count !== null ? <span>{step.row_count} rows</span> : null}
              </div>

              {step.reason ? <p>{step.reason}</p> : null}
              {step.error ? <p className="assistant-step-card__error">{step.error}</p> : null}

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

function StatusBar({ status }: { status: AssistantStatusResponse | null }) {
  if (!status) {
    return (
      <div className="assistant-status">
        <span>Assistant status</span>
        <strong>확인 중</strong>
      </div>
    );
  }

  return (
    <div className="assistant-status">
      <span>
        {status.chat_provider} · {status.chat_model}
      </span>
      <strong>
        pgvector {status.pgvector_available ? "ready" : "unavailable"} · {status.indexed_chunks} chunks
      </strong>
    </div>
  );
}

export function AssistantWorkspace() {
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_MESSAGE]);
  const [draft, setDraft] = useState("");
  const [requestError, setRequestError] = useState<string | null>(null);
  const [status, setStatus] = useState<AssistantStatusResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [isSubmitting, messages]);

  useEffect(() => {
    let ignore = false;

    async function loadStatus() {
      const response = await fetch("/api/assistant/status", { cache: "no-store" });
      const payload = (await response.json().catch(() => null)) as AssistantStatusResponse | null;
      if (!ignore && response.ok && payload) {
        setStatus(payload);
      }
    }

    void loadStatus();
    return () => {
      ignore = true;
    };
  }, []);

  async function submitQuestion(question: string) {
    const normalizedQuestion = question.trim();
    if (!normalizedQuestion || isSubmitting) {
      return;
    }

    setRequestError(null);
    setIsSubmitting(true);
    setMessages((current) => [
      ...current,
      {
        id: createId(),
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
          extractErrorMessage(payload, `Assistant query failed (${response.status})`),
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
        error instanceof Error ? error.message : "질의 처리 중 오류가 발생했습니다.";
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
    <main className="page assistant-page">
      <header className="assistant-page__header">
        <div>
          <span className="eyebrow">Assistant</span>
          <h1>데이터 질의 에이전트</h1>
        </div>
        <StatusBar status={status} />
      </header>

      <section className="assistant-shell">
        <div className="assistant-thread">
          {messages.map((message) => (
            <article
              className={
                message.role === "user"
                  ? "assistant-message assistant-message--user"
                  : `assistant-message assistant-message--${message.role}`
              }
              key={message.id}
            >
              <div className="assistant-message__meta">
                <strong>{message.role === "user" ? "You" : message.role === "system" ? "System" : "Assistant"}</strong>
                {message.response ? (
                  <span>
                    {message.response.citations.length} citations · {message.response.steps.length} steps
                  </span>
                ) : null}
              </div>
              <p>{message.content}</p>
              {message.response ? <MessageTrace response={message.response} /> : null}
            </article>
          ))}

          {isSubmitting ? (
            <article className="assistant-message assistant-message--assistant">
              <div className="assistant-message__meta">
                <strong>Assistant</strong>
                <span>질의 실행 중</span>
              </div>
              <p>DB 도구와 pgvector RAG 검색을 실행하고 있습니다.</p>
            </article>
          ) : null}
          <div ref={messagesEndRef} />
        </div>

        <form className="assistant-composer" onSubmit={handleSubmit}>
          <div className="assistant-samples" aria-label="Sample questions">
            {SAMPLE_QUESTIONS.map((question) => (
              <button
                disabled={isSubmitting}
                key={question}
                onClick={() => setDraft(question)}
                type="button"
              >
                {question}
              </button>
            ))}
          </div>

          <label className="assistant-composer__field">
            <textarea
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={handleTextareaKeyDown}
              placeholder="예: 최근 2주간 활동량이 높지만 부상 위험도도 높은 선수 알려줘."
              rows={4}
              value={draft}
            />
          </label>

          <div className="assistant-composer__footer">
            <span>Enter 전송 · Shift+Enter 줄바꿈</span>
            <button disabled={!draft.trim() || isSubmitting} type="submit">
              {isSubmitting ? "질의 중" : "보내기"}
            </button>
          </div>

          {requestError ? <p className="assistant-composer__error">{requestError}</p> : null}
        </form>
      </section>
    </main>
  );
}
