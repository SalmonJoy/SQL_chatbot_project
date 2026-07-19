from __future__ import annotations

import sys
import os
import time
from dataclasses import replace
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from src.ambiguity_guard import evaluate_ambiguity, prioritize_ambiguous_options  # noqa: E402
from src.answer_generator import generate_answer  # noqa: E402
from src.config import CONFIG  # noqa: E402
from src.context_rewriter import rewrite_follow_up_question  # noqa: E402
from src.conversation_context import build_context_snapshot  # noqa: E402
from src.data_loader import (  # noqa: E402
    load_description_index,
    load_optimized_descriptions,
    load_repository,
    load_user_query_variations,
    merge_repository_with_optimized_descriptions,
)
from src.decision_reviewer import review_decision  # noqa: E402
from src.domain_guard import evaluate_domain  # noqa: E402
from src.formatting import retrieval_rows_for_display, truncate_dataframe  # noqa: E402
from src.multi_intent_guard import evaluate_multi_intent  # noqa: E402
from src.parameter_resolver import ParameterResolver  # noqa: E402
from src.retrieval import HybridRetriever  # noqa: E402
from src.runtime_logger import (  # noqa: E402
    RuntimeLogger,
    base_event,
    dataframe_to_records,
    error_for_log,
    new_request_id,
    retrieval_matches_for_log,
    selected_match_for_log,
)
from src.sql_executor import SQLExecutor  # noqa: E402


runtime_logger = RuntimeLogger(CONFIG)


@st.cache_resource(show_spinner="Loading MiniLM retrieval index...")
def load_services() -> tuple[list[dict], HybridRetriever, SQLExecutor, ParameterResolver]:
    repository = load_repository(CONFIG)
    optimized = load_optimized_descriptions(CONFIG)
    variations = load_user_query_variations(CONFIG)
    merged_repository = merge_repository_with_optimized_descriptions(repository, optimized)
    embeddings, embedding_records = load_description_index(CONFIG)
    retriever = HybridRetriever(merged_repository, variations, embeddings, embedding_records, CONFIG)
    executor = SQLExecutor(merged_repository, CONFIG)
    parameter_resolver = ParameterResolver(CONFIG)
    return merged_repository, retriever, executor, parameter_resolver


def initialize_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_repository_options" not in st.session_state:
        st.session_state.pending_repository_options = None
    if "selected_repository_option" not in st.session_state:
        st.session_state.selected_repository_option = None
    if "conversation_context" not in st.session_state:
        st.session_state.conversation_context = None


def render_sidebar() -> tuple[bool, bool]:
    st.sidebar.title("Retrieval setup")
    st.sidebar.write("**Embedding:** MiniLM")
    st.sidebar.write("**Retrieval:** Hybrid dense + BM25")
    st.sidebar.write(f"**Weights:** dense `{CONFIG.dense_weight:.2f}`, lexical `{CONFIG.lexical_weight:.2f}`")
    st.sidebar.write("**SQL:** Fixed vetted repository")
    st.sidebar.divider()
    gemini_api_key_present = bool(os.getenv("GEMINI_API_KEY"))
    st.sidebar.caption(
        "Gemini can rewrite follow-ups, review close retrieval decisions in Thinking mode, "
        "and phrase final answers. It never generates SQL."
    )
    thinking_mode = st.sidebar.checkbox(
        "Thinking mode",
        value=CONFIG.enable_gemini_decision_review and gemini_api_key_present,
        disabled=not gemini_api_key_present,
        help=(
            "When enabled, the app may use one extra Gemini call for uncertain or conflict-prone matches. "
            "Gemini can only choose from the top vetted repository queries, ask clarification, or block."
        ),
    )
    if not gemini_api_key_present:
        st.sidebar.caption("Set `GEMINI_API_KEY` to enable Thinking mode and Gemini answer wording.")
    elif thinking_mode:
        st.sidebar.caption("Thinking mode is on for close-match review.")
    else:
        st.sidebar.caption("Thinking mode is off; deterministic retrieval/guards decide execution.")
    force_execute = st.sidebar.checkbox(
        "Always execute best match",
        value=False,
        help="Turn on for demos if you want the chatbot to execute even when the confidence margin is low.",
    )
    st.sidebar.divider()
    st.sidebar.markdown("Example questions")
    st.sidebar.code(
        "\n".join(
            [
                "What is the total revenue?",
                "best customers by spending",
                "sales by country",
                "which genres made most money",
                "playlist with most tracks",
            ]
        )
    )
    return force_execute, thinking_mode


def render_retrieval_details(
    matches: list[dict],
    selected_match: dict | None = None,
    decision_review: dict | None = None,
) -> None:
    selected_match = selected_match or matches[0]
    with st.expander("Retrieval details", expanded=False):
        st.dataframe(pd.DataFrame(retrieval_rows_for_display(matches)), use_container_width=True)
        if decision_review:
            st.markdown("Decision review")
            st.json(
                {
                    "status": decision_review.get("status"),
                    "source": decision_review.get("source"),
                    "used_review": decision_review.get("used_review"),
                    "action": decision_review.get("action"),
                    "query_id": decision_review.get("query_id"),
                    "confidence": decision_review.get("confidence"),
                    "reason": decision_review.get("reason"),
                }
            )
        st.code(selected_match["sql"], language="sql")


def render_repository_option_controls(pending: dict) -> None:
    st.markdown("Choose one repository query to execute:")
    for match in pending["matches"]:
        label = f"Run {match['query_id']} - {match['intent']} - score {match['hybrid_score']:.3f}"
        if st.button(
            label,
            key=f"repo_option_{pending['request_id']}_{match['query_id']}",
            use_container_width=True,
        ):
            st.session_state.selected_repository_option = match["query_id"]
            st.rerun()
        st.caption(match["description"])


def render_pending_repository_options() -> None:
    pending = st.session_state.get("pending_repository_options")
    if not pending:
        return

    with st.chat_message("assistant"):
        st.warning("I found multiple plausible repository queries. Pick one to execute.")
        st.caption(pending["reason"])
        render_repository_option_controls(pending)
        st.dataframe(pd.DataFrame(retrieval_rows_for_display(pending["matches"])), use_container_width=True)


def execute_selected_repository_option(selected_query_id: str, force_execute: bool, thinking_mode: bool) -> None:
    pending = st.session_state.get("pending_repository_options")
    if not pending:
        st.session_state.selected_repository_option = None
        return

    selected_match = next(
        (match for match in pending["matches"] if match["query_id"] == selected_query_id),
        None,
    )
    if selected_match is None:
        st.session_state.selected_repository_option = None
        return

    request_id = new_request_id()
    question = pending["question"]
    effective_question = pending.get("effective_question", question)
    request_config = replace(CONFIG, enable_gemini_decision_review=thinking_mode)
    log_event = base_event(request_id, question, force_execute, request_config)
    log_event["event_type"] = "chatbot_repository_selection"
    log_event["selected_from_request_id"] = pending["request_id"]
    log_event["context_rewrite"] = pending.get("context_rewrite")
    log_event["domain_guard"] = pending.get("domain_guard")
    log_event["multi_intent_guard"] = pending.get("multi_intent_guard")
    started_at = time.perf_counter()

    _, _, executor, parameter_resolver = load_services()
    parameter_resolution = parameter_resolver.resolve(selected_match, effective_question)
    decision_reason = f"User selected {selected_match['query_id']} from clarification options."
    ambiguity_guard = evaluate_ambiguity(effective_question, selected_match, pending["matches"])

    log_event["retrieval"] = {
        "status": "manual_selection",
        "elapsed_ms": 0.0,
        "top_k": len(pending["matches"]),
        "matches": retrieval_matches_for_log(pending["matches"]),
        "selected_match": selected_match_for_log(selected_match),
        "parameter_resolution": parameter_resolution.to_log(),
        "ambiguity_guard": ambiguity_guard.to_log(),
        "multi_intent_guard": pending.get("multi_intent_guard"),
        "thinking_mode_enabled": thinking_mode,
        "decision": {
            "should_execute": parameter_resolution.can_execute,
            "retriever_should_execute": False,
            "force_execute": force_execute,
            "reason": decision_reason,
        },
    }

    with st.chat_message("assistant"):
        st.markdown(
            f"Selected repository query: **{selected_match['intent']}** "
            f"(`{selected_match['query_id']}`)."
        )

        if not parameter_resolution.can_execute:
            response_text = (
                "I matched the selected vetted parameterized query, but I need a valid value before executing SQL. "
                + " ".join(parameter_resolution.messages)
            )
            log_event["sql"] = {
                "status": "not_executed",
                "reason": " ".join(parameter_resolution.messages),
                "sql": selected_match.get("sql"),
                "query_id": selected_match.get("query_id"),
                "tables_used": selected_match.get("tables_used", []),
                "expected_columns": selected_match.get("expected_columns", []),
                "parameters": parameter_resolution.parameters,
                "parameter_resolution": parameter_resolution.to_log(),
            }
            log_event["answer"] = {
                "status": "clarification_requested",
                "source": "clarification",
                "gemini_model": CONFIG.gemini_model,
                "text": response_text,
            }
            log_event["elapsed_ms"] = round((time.perf_counter() - started_at) * 1000, 3)
            runtime_logger.write(log_event)

            st.warning("I need a valid parameter value before I execute SQL.")
            st.caption(" ".join(parameter_resolution.messages))
            render_repository_option_controls(pending)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.session_state.selected_repository_option = None
            return

        try:
            sql_started_at = time.perf_counter()
            result_df = executor.execute_query_id(selected_match["query_id"], parameter_resolution.parameters)
            sql_elapsed_ms = round((time.perf_counter() - sql_started_at) * 1000, 3)
            log_event["sql"] = {
                "status": "success",
                "validation_status": "passed_readonly_repository_sql",
                "elapsed_ms": sql_elapsed_ms,
                "query_id": selected_match.get("query_id"),
                "intent": selected_match.get("intent"),
                "category": selected_match.get("category"),
                "sql": selected_match.get("sql"),
                "parameters": parameter_resolution.parameters,
                "parameter_resolution": parameter_resolution.to_log(),
                "tables_used": selected_match.get("tables_used", []),
                "expected_columns": selected_match.get("expected_columns", []),
                "result_columns": list(result_df.columns),
                "result_row_count": len(result_df),
                "result_rows": dataframe_to_records(result_df, CONFIG),
            }

            answer_started_at = time.perf_counter()
            answer, answer_source = generate_answer(question, selected_match, result_df, CONFIG)
            answer_elapsed_ms = round((time.perf_counter() - answer_started_at) * 1000, 3)
            log_event["answer"] = {
                "status": "success",
                "source": answer_source,
                "gemini_model": CONFIG.gemini_model,
                "gemini_api_key_present": bool(os.getenv("GEMINI_API_KEY")),
                "elapsed_ms": answer_elapsed_ms,
                "text": answer,
            }
            log_event["elapsed_ms"] = round((time.perf_counter() - started_at) * 1000, 3)
            runtime_logger.write(log_event)

            st.markdown(answer)
            st.caption(f"Answer source: {answer_source}")

            display_df = truncate_dataframe(result_df, CONFIG.max_result_rows_display)
            st.dataframe(display_df, use_container_width=True)
            if len(display_df) < len(result_df):
                st.caption(f"Showing first {len(display_df)} of {len(result_df)} rows.")

            render_retrieval_details(pending["matches"], selected_match)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.session_state.conversation_context = build_context_snapshot(
                original_question=question,
                effective_question=effective_question,
                match=selected_match,
                sql_parameters=parameter_resolution.parameters,
                result_df=result_df,
                answer=answer,
                config=CONFIG,
            )
            st.session_state.pending_repository_options = None
            st.session_state.selected_repository_option = None
        except Exception as exc:
            log_event.setdefault("sql", {"status": "not_completed"})
            log_event.setdefault("answer", {"status": "not_completed"})
            log_event["error"] = error_for_log(exc)
            log_event["elapsed_ms"] = round((time.perf_counter() - started_at) * 1000, 3)
            runtime_logger.write(log_event)
            st.error(f"Selected query failed: {exc}")
            st.session_state.messages.append(
                {"role": "assistant", "content": f"Selected query failed: {exc}"}
            )
            st.session_state.selected_repository_option = None


def handle_question(question: str, force_execute: bool, thinking_mode: bool) -> None:
    request_id = new_request_id()
    request_config = replace(CONFIG, enable_gemini_decision_review=thinking_mode)
    log_event = base_event(request_id, question, force_execute, request_config)
    started_at = time.perf_counter()
    st.session_state.pending_repository_options = None
    st.session_state.selected_repository_option = None

    repository, retriever, executor, parameter_resolver = load_services()
    _ = repository

    with st.chat_message("user"):
        st.markdown(question)
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("assistant"):
        try:
            retrieval_started_at = time.perf_counter()
            context_rewrite = rewrite_follow_up_question(
                question,
                st.session_state.get("conversation_context"),
                CONFIG,
            )
            effective_question = context_rewrite.effective_question
            log_event["context_rewrite"] = context_rewrite.to_log()

            domain_guard = evaluate_domain(effective_question)
            log_event["domain_guard"] = domain_guard.to_log()
            if domain_guard.should_block:
                retrieval_elapsed_ms = round((time.perf_counter() - retrieval_started_at) * 1000, 3)
                log_event["retrieval"] = {
                    "status": "blocked_by_domain_guard",
                    "elapsed_ms": retrieval_elapsed_ms,
                    "effective_question": effective_question,
                    "domain_guard": domain_guard.to_log(),
                    "thinking_mode_enabled": thinking_mode,
                    "decision": {
                        "should_execute": False,
                        "retriever_should_execute": False,
                        "force_execute": force_execute,
                        "reason": domain_guard.message,
                    },
                }
                log_event["sql"] = {
                    "status": "not_executed",
                    "reason": domain_guard.message,
                    "parameters": {},
                }
                log_event["answer"] = {
                    "status": "domain_blocked",
                    "source": "domain_guard",
                    "gemini_model": CONFIG.gemini_model,
                    "text": domain_guard.message,
                }
                log_event["elapsed_ms"] = round((time.perf_counter() - started_at) * 1000, 3)
                runtime_logger.write(log_event)

                st.warning(domain_guard.message)
                st.session_state.messages.append({"role": "assistant", "content": domain_guard.message})
                return

            matches = retriever.retrieve(effective_question, top_k=5)
            retrieval_elapsed_ms = round((time.perf_counter() - retrieval_started_at) * 1000, 3)
            decision = retriever.decide(matches)
            top = matches[0]
            parameter_resolution = parameter_resolver.resolve(top, effective_question)
            ambiguity_guard = evaluate_ambiguity(effective_question, top, matches)
            multi_intent_guard = evaluate_multi_intent(effective_question)
            should_execute = (
                (force_execute or decision.should_execute)
                and parameter_resolution.can_execute
                and not ambiguity_guard.should_block
                and not multi_intent_guard.should_block
            )
            decision_review = review_decision(
                effective_question,
                matches,
                domain_guard,
                ambiguity_guard,
                multi_intent_guard,
                parameter_resolution,
                should_execute,
                request_config,
            )
            if decision_review.usable:
                if decision_review.action == "execute_repository_query" and decision_review.query_id:
                    reviewed_match = next(
                        (match for match in matches if match["query_id"] == decision_review.query_id),
                        None,
                    )
                    if reviewed_match is not None:
                        top = reviewed_match
                        parameter_resolution = parameter_resolver.resolve(top, effective_question)
                        ambiguity_guard = evaluate_ambiguity(effective_question, top, matches)
                        should_execute = parameter_resolution.can_execute
                elif decision_review.action in {"ask_clarification", "block_multi_intent"}:
                    should_execute = False
                elif decision_review.action == "block_domain":
                    domain_guard = type(domain_guard)(
                        True,
                        "decision_review_block_domain",
                        decision_review.reason or "Gemini decision review classified this as outside the database scope.",
                        matched_domain_terms=domain_guard.matched_domain_terms,
                        offending_clauses=domain_guard.offending_clauses,
                    )
                    should_execute = False

            if not parameter_resolution.can_execute:
                decision_reason = " ".join(parameter_resolution.messages)
            elif decision_review.usable and decision_review.action in {"ask_clarification", "block_domain", "block_multi_intent"}:
                decision_reason = decision_review.reason
            elif should_execute and decision_review.usable and decision_review.action == "execute_repository_query":
                decision_reason = decision_review.reason or "Gemini decision review selected a vetted repository query."
            elif ambiguity_guard.should_block:
                decision_reason = ambiguity_guard.message
            elif multi_intent_guard.should_block:
                decision_reason = multi_intent_guard.message
            else:
                decision_reason = decision.reason

            log_event["retrieval"] = {
                "status": "success",
                "elapsed_ms": retrieval_elapsed_ms,
                "top_k": len(matches),
                "matches": retrieval_matches_for_log(matches),
                "selected_match": selected_match_for_log(top),
                "parameter_resolution": parameter_resolution.to_log(),
                "ambiguity_guard": ambiguity_guard.to_log(),
                "multi_intent_guard": multi_intent_guard.to_log(),
                "domain_guard": domain_guard.to_log(),
                "decision_review": decision_review.to_log(),
                "thinking_mode_enabled": thinking_mode,
                "decision": {
                    "should_execute": should_execute,
                    "retriever_should_execute": decision.should_execute,
                    "force_execute": force_execute,
                    "reason": decision_reason,
                },
            }

            st.markdown(
                f"Matched intent: **{top['intent']}** (`{top['query_id']}`), "
                f"hybrid score `{top['hybrid_score']:.3f}`."
            )
            if context_rewrite.use_rewrite:
                st.caption(f"Interpreted follow-up as: `{effective_question}`")
            if parameter_resolution.parameters:
                st.caption(f"Resolved parameters: `{parameter_resolution.parameters}`")
            if thinking_mode and decision_review.status != "skipped":
                st.caption(
                    "Thinking mode review: "
                    f"{decision_review.action}, confidence `{decision_review.confidence}`."
                )

            if not should_execute:
                if not parameter_resolution.can_execute:
                    response_text = (
                        "I matched a vetted parameterized query, but I need a valid value before executing SQL. "
                        + " ".join(parameter_resolution.messages)
                    )
                else:
                    response_text = "I found multiple plausible repository queries and asked for clarification."
                log_event["sql"] = {
                    "status": "not_executed",
                    "reason": decision_reason,
                    "sql": top.get("sql"),
                    "query_id": top.get("query_id"),
                    "tables_used": top.get("tables_used", []),
                    "expected_columns": top.get("expected_columns", []),
                    "parameters": parameter_resolution.parameters,
                    "parameter_resolution": parameter_resolution.to_log(),
                }
                log_event["answer"] = {
                    "status": "clarification_requested",
                    "source": "clarification",
                    "gemini_model": CONFIG.gemini_model,
                    "text": response_text,
                }
                log_event["elapsed_ms"] = round((time.perf_counter() - started_at) * 1000, 3)
                runtime_logger.write(log_event)
                option_matches = prioritize_ambiguous_options(effective_question, matches[:5])
                st.session_state.pending_repository_options = {
                    "request_id": request_id,
                    "question": question,
                    "effective_question": effective_question,
                    "context_rewrite": context_rewrite.to_log(),
                    "domain_guard": domain_guard.to_log(),
                    "multi_intent_guard": multi_intent_guard.to_log(),
                    "reason": decision_reason,
                    "matches": option_matches,
                }

                if not parameter_resolution.can_execute:
                    st.warning("I need a valid parameter value before I execute SQL.")
                elif ambiguity_guard.should_block:
                    st.warning("I need clarification before I execute SQL.")
                elif multi_intent_guard.should_block:
                    st.warning("Please choose one repository query to execute.")
                else:
                    st.warning(
                        "I found multiple plausible repository queries. Please clarify or rephrase before I execute SQL."
                    )
                st.caption(decision_reason)
                render_repository_option_controls(st.session_state.pending_repository_options)
                st.dataframe(pd.DataFrame(retrieval_rows_for_display(matches[:3])), use_container_width=True)
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": response_text,
                    }
                )
                return

            sql_started_at = time.perf_counter()
            result_df = executor.execute_query_id(top["query_id"], parameter_resolution.parameters)
            sql_elapsed_ms = round((time.perf_counter() - sql_started_at) * 1000, 3)
            log_event["sql"] = {
                "status": "success",
                "validation_status": "passed_readonly_repository_sql",
                "elapsed_ms": sql_elapsed_ms,
                "query_id": top.get("query_id"),
                "intent": top.get("intent"),
                "category": top.get("category"),
                "sql": top.get("sql"),
                "parameters": parameter_resolution.parameters,
                "parameter_resolution": parameter_resolution.to_log(),
                "tables_used": top.get("tables_used", []),
                "expected_columns": top.get("expected_columns", []),
                "result_columns": list(result_df.columns),
                "result_row_count": len(result_df),
                "result_rows": dataframe_to_records(result_df, CONFIG),
            }

            answer_started_at = time.perf_counter()
            answer, answer_source = generate_answer(question, top, result_df, CONFIG)
            answer_elapsed_ms = round((time.perf_counter() - answer_started_at) * 1000, 3)
            log_event["answer"] = {
                "status": "success",
                "source": answer_source,
                "gemini_model": CONFIG.gemini_model,
                "gemini_api_key_present": bool(os.getenv("GEMINI_API_KEY")),
                "elapsed_ms": answer_elapsed_ms,
                "text": answer,
            }
            log_event["elapsed_ms"] = round((time.perf_counter() - started_at) * 1000, 3)
            runtime_logger.write(log_event)

            st.markdown(answer)
            st.caption(f"Answer source: {answer_source}")

            display_df = truncate_dataframe(result_df, CONFIG.max_result_rows_display)
            st.dataframe(display_df, use_container_width=True)
            if len(display_df) < len(result_df):
                st.caption(f"Showing first {len(display_df)} of {len(result_df)} rows.")

            render_retrieval_details(matches, top, decision_review.to_log())
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.session_state.conversation_context = build_context_snapshot(
                original_question=question,
                effective_question=effective_question,
                match=top,
                sql_parameters=parameter_resolution.parameters,
                result_df=result_df,
                answer=answer,
                config=CONFIG,
            )
        except Exception as exc:
            log_event.setdefault("retrieval", {"status": "not_completed"})
            log_event.setdefault("sql", {"status": "not_completed"})
            log_event.setdefault("answer", {"status": "not_completed"})
            log_event["error"] = error_for_log(exc)
            log_event["elapsed_ms"] = round((time.perf_counter() - started_at) * 1000, 3)
            runtime_logger.write(log_event)
            st.error(f"Request failed: {exc}")
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"Request failed: {exc}",
                }
            )


def main() -> None:
    st.set_page_config(page_title="NL-to-SQL Insight Chatbot", page_icon="🎧", layout="wide")
    initialize_state()
    force_execute, thinking_mode = render_sidebar()

    st.title("Natural Language to SQL Insight Chatbot")
    st.caption(
        "Ask a business question. The app retrieves a vetted SQL query, executes it on Chinook SQLite, "
        "and uses Gemini only for follow-up rewriting, optional Thinking mode review, and grounded answer wording."
    )

    try:
        load_services()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.code("python scripts/build_index.py", language="bash")
        st.stop()
    except Exception as exc:
        st.error(f"Startup failed: {exc}")
        st.stop()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    selected_query_id = st.session_state.get("selected_repository_option")
    if selected_query_id:
        execute_selected_repository_option(selected_query_id, force_execute, thinking_mode)
    else:
        render_pending_repository_options()

    question = st.chat_input("Ask about sales, customers, products, artists, support reps, or playlists")
    if question:
        handle_question(question, force_execute, thinking_mode)


if __name__ == "__main__":
    main()
