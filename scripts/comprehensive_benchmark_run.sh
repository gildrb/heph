#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd -P)"

UV_BIN="${HEPH_BENCHMARK_UV:-uv}"
PYTHON_BIN="${HEPH_BENCHMARK_PYTHON:-}"

OUTPUT_DIR="${HEPH_BENCHMARK_OUTPUT_DIR:-${REPO_ROOT}/.artifacts/comprehensive-benchmark}"
PROMPT_PATH="${REPO_ROOT}/benchmarks/model-evaluation-prompt.md"
MODEL_LABEL="comprehensive-benchmark"

FIXTURE_MODE=0
OFFLINE=0
SKIP_DEPENDENCY_CHECKS=0
DEPENDENCY_CHECK_ONLY=0
REQUIRE_BEIR_EXTRA=0
REQUIRE_VISUALIZATION_EXTRA=0
VALIDATE_REPRODUCIBILITY=0
VISUALIZE=0

SKIP_BEIR=0
SKIP_STANDARD_RAG=0
SKIP_NATIVE=0
SKIP_PUBLIC_ACADEMIC=0
SKIP_PUBLIC_MATERIALIZATION=0

BEIR_DATASET="beir/nfcorpus"
BEIR_SOURCE_DIR=""
BEIR_SOURCE_ZIP=""
BEIR_DOWNLOAD_URL=""
STANDARD_RAG_DATASET="ms-marco"
STANDARD_RAG_MANIFEST=""
NATIVE_SUITE="${REPO_ROOT}/benchmarks/academic"
PUBLIC_ACADEMIC_MANIFEST="${REPO_ROOT}/benchmarks/public-academic/manifest.json"
PUBLIC_ACADEMIC_SUITE=""
PUBLIC_ACADEMIC_ARMORY=""
PUBLIC_ACADEMIC_CASES_DIR=""

PUBLIC_MIN_RETRIEVAL_CASES=25
PUBLIC_MIN_MATERIAL_ROLE_CASES=15
PUBLIC_MIN_DOCUMENT_UNDERSTANDING_CASES=10
PUBLIC_MIN_DOMAINS=3
PUBLIC_MIN_MATERIAL_ROLES=4
PUBLIC_MIN_SOURCE_ORGANIZATIONS=3

CURRENT_PHASE="setup"
RUN_LOG=""
STATUS_FILE=""
INITIAL_GIT_STATUS=""
RUNNER_REPORTS=()

usage() {
  cat <<'USAGE'
Usage: scripts/comprehensive_benchmark_run.sh [options]

Runs the ordered benchmark workflow:
  materialization -> external adapters -> native suite -> public-academic runner -> summary

Core options:
  --output-dir PATH             Run-scoped artifact directory under /tmp or .artifacts
  --prompt PATH                 Model evaluation prompt to record by path and SHA-256 hash
  --model-label LABEL           Optional model/evaluation label recorded in runner reports
  --fixture-mode                Generate small local fixtures under --output-dir; no downloads
  --offline                     Forbid download/materialization phases that require network access
  --skip-downloads              Alias for --offline
  --validate-reproducibility    Run deterministic-field reproducibility checks in runners
  --visualize                   Ask the Markdown summary for visualization availability notes

Dependency options:
  --require-beir-extra          Require the optional BEIR extra before running
  --require-visualization-extra Require matplotlib before --visualize output
  --skip-dependency-checks      Skip optional dependency import checks
  --dependency-check-only       Only run requested dependency checks, then exit

Dataset selection:
  --beir-dataset ID             BEIR dataset id, e.g. beir/nfcorpus
  --beir-source-dir PATH        Local extracted BEIR source directory
  --beir-source-zip PATH        Local BEIR zip fixture
  --beir-download-url URL       Explicit HTTPS BEIR dataset zip URL
  --standard-rag-dataset ID     Standard RAG dataset id, e.g. ms-marco
  --standard-rag-manifest PATH  Local standard RAG manifest
  --native-suite PATH           Hephaistos native benchmark suite path
  --public-academic-manifest PATH
                                Public academic manifest for materialization
  --public-academic-suite PATH  Pre-generated public-academic case suite with readiness_report.json
  --public-academic-armory PATH Materialized public-academic armory path
  --public-academic-cases-dir PATH
                                Generated public-academic case directory

Skip controls:
  --skip-beir
  --skip-standard-rag
  --skip-native
  --skip-public-academic
  --skip-public-materialization

Fixture public-academic minimum overrides:
  --public-min-retrieval-cases N
  --public-min-material-role-cases N
  --public-min-document-understanding-cases N
  --public-min-domains N
  --public-min-material-roles N
  --public-min-source-organizations N

Generated artifacts are contained under the configured output directory. The script snapshots
repository status before and after the run and fails if generated files pollute the repository.

Environment overrides:
  HEPH_BENCHMARK_UV PATH         uv executable to use; defaults to uv
  HEPH_BENCHMARK_PYTHON PATH     Explicit Python executable for helper and dependency checks;
                                 unset uses uv run python from the project environment
USAGE
}

redact_text() {
  local text="$1"
  local name
  local value
  while IFS='=' read -r name value; do
    case "${name}" in
      *API_KEY*|*AUTH*|*CREDENTIAL*|*DSN*|*KEY*|*PASSWORD*|*SECRET*|*TOKEN*)
        if [[ "${#value}" -ge 4 ]]; then
          text="${text//${value}/[REDACTED]}"
        fi
        ;;
    esac
  done < <(env)
  printf '%s' "${text}"
}

log() {
  local message
  message="$(redact_text "$*")"
  if [[ -n "${RUN_LOG}" ]]; then
    printf '%s\n' "${message}" | tee -a "${RUN_LOG}"
  else
    printf '%s\n' "${message}"
  fi
}

write_status() {
  local status="$1"
  local phase="$2"
  local message="$3"
  if [[ -z "${STATUS_FILE}" ]]; then
    return
  fi
  {
    printf 'status=%s\n' "${status}"
    printf 'phase=%s\n' "${phase}"
    printf 'message=%s\n' "$(redact_text "${message}")"
  } > "${STATUS_FILE}"
}

fail() {
  local message="$1"
  local code="${2:-2}"
  write_status "failed" "${CURRENT_PHASE}" "${message}"
  log "error phase=${CURRENT_PHASE} ${message}"
  exit "${code}"
}

absolute_path() {
  local raw="$1"
  if [[ "${raw}" = /* ]]; then
    printf '%s\n' "${raw}"
  else
    printf '%s/%s\n' "${REPO_ROOT}" "${raw}"
  fi
}

resolve_existing_file() {
  local raw="$1"
  local absolute
  absolute="$(absolute_path "${raw}")"
  if [[ ! -f "${absolute}" ]]; then
    fail "required file does not exist: ${absolute}"
  fi
  local parent
  local base
  parent="$(dirname "${absolute}")"
  base="$(basename "${absolute}")"
  printf '%s/%s\n' "$(cd "${parent}" && pwd -P)" "${base}"
}

run_python() {
  if [[ -n "${PYTHON_BIN}" ]]; then
    "${PYTHON_BIN}" "$@"
  else
    "${UV_BIN}" run python "$@"
  fi
}

prepare_output_dir() {
  local raw
  raw="$(absolute_path "${OUTPUT_DIR}")"
  if [[ "${raw}" == "/" || "${raw}" == "/tmp" || "${raw}" == "${REPO_ROOT}/.artifacts" ]]; then
    fail "output directory must be run-scoped, not ${raw}"
  fi
  case "${raw}" in
    /tmp/*|"${REPO_ROOT}"/.artifacts/*) ;;
    *)
      fail "output directory must be under /tmp or ${REPO_ROOT}/.artifacts: ${raw}"
      ;;
  esac
  if [[ -L "${raw}" ]]; then
    fail "refusing symlinked output directory: ${raw}"
  fi
  if [[ -e "${raw}" && ! -d "${raw}" ]]; then
    fail "output path exists and is not a directory: ${raw}"
  fi
  if [[ -d "${raw}" && -n "$(find "${raw}" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    fail "output directory is not empty; choose a new run-scoped path: ${raw}"
  fi
  mkdir -p "${raw}"
  OUTPUT_DIR="$(cd "${raw}" && pwd -P)"
  RUN_LOG="${OUTPUT_DIR}/comprehensive-benchmark.log"
  STATUS_FILE="${OUTPUT_DIR}/run-status.txt"
  : > "${RUN_LOG}"
  write_status "running" "setup" "initialized"
}

prompt_hash() {
  run_python -c \
    'from pathlib import Path; import hashlib; import sys; print(hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest())' \
    "$1"
}

check_optional_module() {
  local module="$1"
  local extra="$2"
  if [[ "${SKIP_DEPENDENCY_CHECKS}" -eq 1 ]]; then
    return
  fi
  local output
  local status
  set +e
  output="$(run_python -c \
    "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('${module}') is not None else 1)" \
    2>&1)"
  status=$?
  set -e
  if [[ "${status}" -ne 0 ]]; then
    if [[ -n "${output}" ]]; then
      log "${output}"
    fi
    fail "missing optional dependency '${module}'. Install with: uv sync --extra ${extra}"
  fi
}

run_dependency_checks() {
  CURRENT_PHASE="dependency-checks"
  if [[ "${REQUIRE_BEIR_EXTRA}" -eq 1 ]]; then
    check_optional_module "beir" "beir"
  fi
  if [[ "${REQUIRE_VISUALIZATION_EXTRA}" -eq 1 || "${VISUALIZE}" -eq 1 ]]; then
    check_optional_module "matplotlib" "visualization"
  fi
  log "phase=dependency-checks status=completed"
}

start_phase() {
  CURRENT_PHASE="$1"
  write_status "running" "${CURRENT_PHASE}" ""
  log "phase=${CURRENT_PHASE} status=started"
}

finish_phase() {
  log "phase=${CURRENT_PHASE} status=completed"
}

run_command() {
  local output
  local status
  log "command=$*"
  set +e
  output="$("$@" 2>&1)"
  status=$?
  set -e
  if [[ -n "${output}" ]]; then
    log "${output}"
  fi
  if [[ "${status}" -ne 0 ]]; then
    fail "command failed with exit ${status}: $*" "${status}"
  fi
}

create_fixture_inputs() {
  local fixture_dir="${OUTPUT_DIR}/fixtures"
  local beir_dir="${fixture_dir}/beir"
  local public_suite="${fixture_dir}/public-academic-suite"
  local standard_manifest="${fixture_dir}/standard-rag-manifest.json"
  mkdir -p "${beir_dir}/qrels" "${public_suite}/armory/materials" "${public_suite}/armory/.hephaistos"

  cat > "${beir_dir}/corpus.jsonl" <<'JSONL'
{"_id":"alpha","title":"Alpha Notes","text":"Alpha deterministic benchmark retrieval evidence."}
{"_id":"beta","title":"Beta Distractor","text":"Beta distractor material."}
JSONL
  cat > "${beir_dir}/queries.jsonl" <<'JSONL'
{"_id":"q1","text":"alpha deterministic benchmark retrieval evidence"}
JSONL
  cat > "${beir_dir}/qrels/test.tsv" <<'TSV'
query-id	corpus-id	score
q1	alpha	1
q1	beta	0
TSV

  cat > "${standard_manifest}" <<'JSON'
{
  "dataset": "fixture-standard-rag",
  "domain": "fixture",
  "documents": [
    {
      "id": "alpha",
      "title": "Alpha Standard RAG",
      "text": "Alpha standard RAG evidence supports deterministic fixture execution."
    },
    {
      "id": "beta",
      "title": "Beta Standard RAG",
      "text": "Beta distractor text."
    }
  ],
  "queries": [
    {
      "id": "q1",
      "question": "Which standard RAG document contains alpha deterministic evidence?",
      "relevant_documents": {"alpha": 1, "beta": 0}
    }
  ],
  "split": "fixture",
  "task_type": "question-answering"
}
JSON

  cat > "${public_suite}/armory/.hephaistos/armory.toml" <<'TOML'
version = 1
created_at = "1970-01-01T00:00:00+00:00"
TOML
  cat > "${public_suite}/armory/materials/public-alpha.md" <<'MD'
# Public Alpha

Public academic alpha fixture material for deterministic benchmark execution.
MD
  cat > "${public_suite}/rag.jsonl" <<'JSONL'
{"id":"public-alpha","domain":"fixture","task":"single-source","query":"public academic alpha fixture material","expected":["materials/public-alpha.md"],"top_k":5}
JSONL
  cat > "${public_suite}/readiness_report.json" <<JSON
{
  "status": "passed",
  "benchmark_ready": true,
  "armory_path": "${public_suite}/armory",
  "generated_files": {
    "rag": "${public_suite}/rag.jsonl"
  }
}
JSON

  BEIR_DATASET="beir/fixture"
  BEIR_SOURCE_DIR="${beir_dir}"
  STANDARD_RAG_DATASET="fixture-standard-rag"
  STANDARD_RAG_MANIFEST="${standard_manifest}"
  PUBLIC_ACADEMIC_SUITE="${public_suite}"
  SKIP_PUBLIC_MATERIALIZATION=1
}

materialize_public_academic() {
  if [[ "${SKIP_PUBLIC_ACADEMIC}" -eq 1 ]]; then
    return
  fi
  if [[ -n "${PUBLIC_ACADEMIC_SUITE}" ]]; then
    log "public_academic_suite=${PUBLIC_ACADEMIC_SUITE}"
    return
  fi
  if [[ "${OFFLINE}" -eq 1 || "${SKIP_PUBLIC_MATERIALIZATION}" -eq 1 ]]; then
    fail "offline or skipped public materialization requires --public-academic-suite"
  fi
  PUBLIC_ACADEMIC_ARMORY="${PUBLIC_ACADEMIC_ARMORY:-${OUTPUT_DIR}/public-academic/armory}"
  PUBLIC_ACADEMIC_CASES_DIR="${PUBLIC_ACADEMIC_CASES_DIR:-${OUTPUT_DIR}/public-academic/cases}"
  run_command "${UV_BIN}" run python -m scripts.materialize_public_corpus \
    "${PUBLIC_ACADEMIC_MANIFEST}" \
    "${PUBLIC_ACADEMIC_ARMORY}" \
    --json-report "${OUTPUT_DIR}/reports/public-academic-materialize.json"
  run_command "${UV_BIN}" run python -m scripts.generate_public_academic_benchmark_cases \
    "${PUBLIC_ACADEMIC_MANIFEST}" \
    "${PUBLIC_ACADEMIC_ARMORY}" \
    --output-dir "${PUBLIC_ACADEMIC_CASES_DIR}" \
    --json-report "${OUTPUT_DIR}/reports/public-academic-readiness.json" \
    --min-retrieval-cases "${PUBLIC_MIN_RETRIEVAL_CASES}" \
    --min-material-role-cases "${PUBLIC_MIN_MATERIAL_ROLE_CASES}" \
    --min-document-understanding-cases "${PUBLIC_MIN_DOCUMENT_UNDERSTANDING_CASES}" \
    --min-domains "${PUBLIC_MIN_DOMAINS}" \
    --min-material-roles "${PUBLIC_MIN_MATERIAL_ROLES}" \
    --min-source-organizations "${PUBLIC_MIN_SOURCE_ORGANIZATIONS}"
  PUBLIC_ACADEMIC_SUITE="${PUBLIC_ACADEMIC_CASES_DIR}"
}

run_external_adapter_phase() {
  if [[ "${SKIP_BEIR}" -eq 0 ]]; then
    local beir_suite="${OUTPUT_DIR}/suites/beir"
    local beir_command=(
      "${UV_BIN}" run python -m scripts.external_benchmarks.beir_adapter
      "${BEIR_DATASET}"
      --output "${beir_suite}"
      --json-report "${OUTPUT_DIR}/reports/beir-adapter.json"
    )
    if [[ -n "${BEIR_SOURCE_DIR}" ]]; then
      beir_command+=(--source-dir "${BEIR_SOURCE_DIR}")
    elif [[ -n "${BEIR_SOURCE_ZIP}" ]]; then
      beir_command+=(--source-zip "${BEIR_SOURCE_ZIP}")
    elif [[ -n "${BEIR_DOWNLOAD_URL}" ]]; then
      beir_command+=(--download-url "${BEIR_DOWNLOAD_URL}")
    elif [[ "${OFFLINE}" -eq 1 ]]; then
      fail "offline BEIR runs require --beir-source-dir or --beir-source-zip"
    fi
    run_command "${beir_command[@]}"
    BEIR_SUITE="${beir_suite}"
  fi

  if [[ "${SKIP_STANDARD_RAG}" -eq 0 ]]; then
    if [[ -z "${STANDARD_RAG_MANIFEST}" ]]; then
      fail "standard RAG phase requires --standard-rag-manifest or --fixture-mode"
    fi
    local standard_suite="${OUTPUT_DIR}/suites/standard-rag"
    run_command "${UV_BIN}" run python -m scripts.external_benchmarks.standard_rag_adapter \
      "${STANDARD_RAG_DATASET}" \
      --manifest "${STANDARD_RAG_MANIFEST}" \
      --output "${standard_suite}" \
      --json-report "${OUTPUT_DIR}/reports/standard-rag-adapter.json"
    STANDARD_RAG_SUITE="${standard_suite}"
  fi
}

run_benchmark_runner() {
  local benchmark_type="$1"
  local dataset="$2"
  local suite="$3"
  local report_path="$4"
  if [[ "${VALIDATE_REPRODUCIBILITY}" -eq 1 ]]; then
    run_command "${UV_BIN}" run python -m scripts.run_external_benchmarks \
      "${benchmark_type}" "${dataset}" \
      --suite "${suite}" \
      --prompt "${PROMPT_PATH}" \
      --model-label "${MODEL_LABEL}" \
      --validate-reproducibility \
      --json-report "${report_path}"
  else
    run_command "${UV_BIN}" run python -m scripts.run_external_benchmarks \
      "${benchmark_type}" "${dataset}" \
      --suite "${suite}" \
      --prompt "${PROMPT_PATH}" \
      --model-label "${MODEL_LABEL}" \
      --json-report "${report_path}"
  fi
}

run_external_runner_phase() {
  if [[ "${SKIP_BEIR}" -eq 0 ]]; then
    run_benchmark_runner \
      "beir" \
      "${BEIR_DATASET}" \
      "${BEIR_SUITE}" \
      "${OUTPUT_DIR}/reports/beir-runner.json"
    RUNNER_REPORTS+=("${OUTPUT_DIR}/reports/beir-runner.json")
  fi

  if [[ "${SKIP_STANDARD_RAG}" -eq 0 ]]; then
    run_benchmark_runner \
      "standard-rag" \
      "${STANDARD_RAG_DATASET}" \
      "${STANDARD_RAG_SUITE}" \
      "${OUTPUT_DIR}/reports/standard-rag-runner.json"
    RUNNER_REPORTS+=("${OUTPUT_DIR}/reports/standard-rag-runner.json")
  fi
}

run_native_runner_phase() {
  if [[ "${SKIP_NATIVE}" -eq 0 ]]; then
    run_benchmark_runner \
      "heph-native" \
      "academic" \
      "${NATIVE_SUITE}" \
      "${OUTPUT_DIR}/reports/heph-native-runner.json"
    RUNNER_REPORTS+=("${OUTPUT_DIR}/reports/heph-native-runner.json")
  fi
}

run_public_academic_runner_phase() {
  if [[ "${SKIP_PUBLIC_ACADEMIC}" -eq 0 ]]; then
    if [[ -z "${PUBLIC_ACADEMIC_SUITE}" ]]; then
      fail "public-academic phase requires materialized suite"
    fi
    run_benchmark_runner \
      "public-academic" \
      "public-academic" \
      "${PUBLIC_ACADEMIC_SUITE}" \
      "${OUTPUT_DIR}/reports/public-academic-runner.json"
    RUNNER_REPORTS+=("${OUTPUT_DIR}/reports/public-academic-runner.json")
  fi
}

run_summary_phase() {
  if [[ "${#RUNNER_REPORTS[@]}" -eq 0 ]]; then
    fail "no runner reports were produced for summary generation"
  fi
  if [[ "${VISUALIZE}" -eq 1 ]]; then
    mkdir -p "${OUTPUT_DIR}/summary"
    run_command "${UV_BIN}" run python -m scripts.generate_benchmark_summary \
      "${RUNNER_REPORTS[@]}" \
      --output "${OUTPUT_DIR}/summary/benchmark-summary.md" \
      --visualize
  else
    mkdir -p "${OUTPUT_DIR}/summary"
    run_command "${UV_BIN}" run python -m scripts.generate_benchmark_summary \
      "${RUNNER_REPORTS[@]}" \
      --output "${OUTPUT_DIR}/summary/benchmark-summary.md"
  fi
}

snapshot_git_status() {
  if [[ "${HEPH_BENCHMARK_SKIP_GIT_CHECK:-0}" = "1" ]]; then
    INITIAL_GIT_STATUS=""
    return
  fi
  INITIAL_GIT_STATUS="$(git -C "${REPO_ROOT}" status --porcelain --untracked-files=all)"
}

verify_git_status_unchanged() {
  if [[ "${HEPH_BENCHMARK_SKIP_GIT_CHECK:-0}" = "1" ]]; then
    return
  fi
  local final_status
  final_status="$(git -C "${REPO_ROOT}" status --porcelain --untracked-files=all)"
  if [[ "${final_status}" != "${INITIAL_GIT_STATUS}" ]]; then
    fail "repository status changed; generated artifacts must stay in ${OUTPUT_DIR}"
  fi
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --prompt)
      PROMPT_PATH="$2"
      shift 2
      ;;
    --model-label)
      MODEL_LABEL="$2"
      shift 2
      ;;
    --fixture-mode)
      FIXTURE_MODE=1
      shift
      ;;
    --offline|--skip-downloads)
      OFFLINE=1
      shift
      ;;
    --validate-reproducibility)
      VALIDATE_REPRODUCIBILITY=1
      shift
      ;;
    --visualize)
      VISUALIZE=1
      shift
      ;;
    --require-beir-extra)
      REQUIRE_BEIR_EXTRA=1
      shift
      ;;
    --require-visualization-extra)
      REQUIRE_VISUALIZATION_EXTRA=1
      shift
      ;;
    --skip-dependency-checks)
      SKIP_DEPENDENCY_CHECKS=1
      shift
      ;;
    --dependency-check-only)
      DEPENDENCY_CHECK_ONLY=1
      shift
      ;;
    --beir-dataset)
      BEIR_DATASET="$2"
      shift 2
      ;;
    --beir-source-dir)
      BEIR_SOURCE_DIR="$(absolute_path "$2")"
      shift 2
      ;;
    --beir-source-zip)
      BEIR_SOURCE_ZIP="$(absolute_path "$2")"
      shift 2
      ;;
    --beir-download-url)
      BEIR_DOWNLOAD_URL="$2"
      shift 2
      ;;
    --standard-rag-dataset)
      STANDARD_RAG_DATASET="$2"
      shift 2
      ;;
    --standard-rag-manifest)
      STANDARD_RAG_MANIFEST="$(absolute_path "$2")"
      shift 2
      ;;
    --native-suite)
      NATIVE_SUITE="$(absolute_path "$2")"
      shift 2
      ;;
    --public-academic-manifest)
      PUBLIC_ACADEMIC_MANIFEST="$(absolute_path "$2")"
      shift 2
      ;;
    --public-academic-suite)
      PUBLIC_ACADEMIC_SUITE="$(absolute_path "$2")"
      shift 2
      ;;
    --public-academic-armory)
      PUBLIC_ACADEMIC_ARMORY="$(absolute_path "$2")"
      shift 2
      ;;
    --public-academic-cases-dir)
      PUBLIC_ACADEMIC_CASES_DIR="$(absolute_path "$2")"
      shift 2
      ;;
    --skip-beir)
      SKIP_BEIR=1
      shift
      ;;
    --skip-standard-rag)
      SKIP_STANDARD_RAG=1
      shift
      ;;
    --skip-native)
      SKIP_NATIVE=1
      shift
      ;;
    --skip-public-academic)
      SKIP_PUBLIC_ACADEMIC=1
      shift
      ;;
    --skip-public-materialization)
      SKIP_PUBLIC_MATERIALIZATION=1
      shift
      ;;
    --public-min-retrieval-cases)
      PUBLIC_MIN_RETRIEVAL_CASES="$2"
      shift 2
      ;;
    --public-min-material-role-cases)
      PUBLIC_MIN_MATERIAL_ROLE_CASES="$2"
      shift 2
      ;;
    --public-min-document-understanding-cases)
      PUBLIC_MIN_DOCUMENT_UNDERSTANDING_CASES="$2"
      shift 2
      ;;
    --public-min-domains)
      PUBLIC_MIN_DOMAINS="$2"
      shift 2
      ;;
    --public-min-material-roles)
      PUBLIC_MIN_MATERIAL_ROLES="$2"
      shift 2
      ;;
    --public-min-source-organizations)
      PUBLIC_MIN_SOURCE_ORGANIZATIONS="$2"
      shift 2
      ;;
    *)
      fail "unknown option: $1"
      ;;
  esac
done

run_dependency_checks
if [[ "${DEPENDENCY_CHECK_ONLY}" -eq 1 ]]; then
  exit 0
fi

PROMPT_PATH="$(resolve_existing_file "${PROMPT_PATH}")"
prepare_output_dir
PROMPT_HASH="$(prompt_hash "${PROMPT_PATH}")"
snapshot_git_status
mkdir -p "${OUTPUT_DIR}/reports" "${OUTPUT_DIR}/suites"

log "comprehensive_benchmark_run output_dir=${OUTPUT_DIR}"
log "prompt_path=${PROMPT_PATH} prompt_hash=${PROMPT_HASH} model_label=${MODEL_LABEL}"

start_phase "materialization"
if [[ "${FIXTURE_MODE}" -eq 1 ]]; then
  create_fixture_inputs
fi
materialize_public_academic
finish_phase

start_phase "external-adapters"
run_external_adapter_phase
run_external_runner_phase
finish_phase

start_phase "native"
run_native_runner_phase
finish_phase

start_phase "public-academic"
run_public_academic_runner_phase
finish_phase

start_phase "summary"
run_summary_phase
finish_phase

CURRENT_PHASE="repo-cleanliness"
verify_git_status_unchanged
write_status "success" "complete" "summary=${OUTPUT_DIR}/summary/benchmark-summary.md"
log "status=success summary=${OUTPUT_DIR}/summary/benchmark-summary.md"
