import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
PIPELINE_ROOT = Path("skillforge Ai") / "skillforge Ai"

INPUT_RESUME = Path("main_Resume-2.pdf")
INPUT_JOB_DESC = Path("System Software Engineer.pdf")
OUTPUT_DIR = Path("output")
OUTPUT_DIR_MODULE_1 = OUTPUT_DIR / "resume" / "module_1"
OUTPUT_DIR_MODULE_2 = OUTPUT_DIR / "resume" / "module_2"
OUTPUT_DIR_MODULE_2_A = OUTPUT_DIR_MODULE_2 / "A"
OUTPUT_DIR_MODULE_2_B = OUTPUT_DIR_MODULE_2 / "B"
OUTPUT_DIR_MODULE_3 = OUTPUT_DIR / "jd" / "module_3"
OUTPUT_DIR_MODULE_3_COMBINED = OUTPUT_DIR_MODULE_3 / "COMBINED"
OUTPUT_DIR_MODULE_3_KEYWORD = OUTPUT_DIR_MODULE_3 / "module2_Keyword"
OUTPUT_DIR_MODULE_3_SEMANTIC = OUTPUT_DIR_MODULE_3 / "module2_semantic"
OUTPUT_DIR_MODULE_4 = OUTPUT_DIR / "module_4"
OUTPUT_DIR_MODULE_5 = OUTPUT_DIR / "module_5"
OUTPUT_DIR_MODULE_6 = OUTPUT_DIR / "module_6"
OUTPUT_DIR_MODULE_6_GRAPHS = OUTPUT_DIR_MODULE_6 / "Graphs"
OUTPUT_DIR_MODULE_7 = OUTPUT_DIR / "module_7"
OUTPUT_DIR_MODULE_8 = OUTPUT_DIR / "module_8"


def _repo_path(path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_DIR / candidate


def _display_path(path: Path | str) -> str:
    return str(Path(path))


def _require_exists(path: Path | str, label: str) -> None:
    resolved_path = _repo_path(path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"{label} not found: {resolved_path}")


def _run_module(script: Path | str, *args: Path | str) -> None:
    _require_exists(script, "Pipeline module")
    subprocess.run(
        [sys.executable, _display_path(script), *(_display_path(arg) for arg in args)],
        cwd=PROJECT_DIR,
        check=True,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full SkillForge AI pipeline.")
    parser.add_argument("--resume", type=Path, default=INPUT_RESUME, help=f"Resume input path. Default: {INPUT_RESUME}")
    parser.add_argument(
        "--job-desc",
        type=Path,
        default=INPUT_JOB_DESC,
        help=f"Job description input path. Default: {INPUT_JOB_DESC}",
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help=f"Output directory. Default: {OUTPUT_DIR}")
    return parser.parse_args()


def run_pipeline(input_dir_resume, input_dir_job_desc, output_dir):
    input_dir_resume = Path(input_dir_resume)
    input_dir_job_desc = Path(input_dir_job_desc)
    output_dir = Path(output_dir)

    _require_exists(input_dir_resume, "Resume input")
    _require_exists(input_dir_job_desc, "Job description input")

    output_directories = (
        output_dir,
        OUTPUT_DIR_MODULE_1,
        OUTPUT_DIR_MODULE_2,
        OUTPUT_DIR_MODULE_2_A,
        OUTPUT_DIR_MODULE_2_B,
        OUTPUT_DIR_MODULE_3,
        OUTPUT_DIR_MODULE_3_COMBINED,
        OUTPUT_DIR_MODULE_3_KEYWORD,
        OUTPUT_DIR_MODULE_3_SEMANTIC,
        OUTPUT_DIR_MODULE_4,
        OUTPUT_DIR_MODULE_5,
        OUTPUT_DIR_MODULE_6,
        OUTPUT_DIR_MODULE_6_GRAPHS,
        OUTPUT_DIR_MODULE_7,
        OUTPUT_DIR_MODULE_8,
    )
    for directory in output_directories:
        _repo_path(directory).mkdir(parents=True, exist_ok=True)

    module_1_script = PIPELINE_ROOT / "module_1_Parse_extractor" / "main_extraction.py"
    _run_module(module_1_script, input_dir_resume, OUTPUT_DIR_MODULE_1)

    module_2_A_script = PIPELINE_ROOT / "module2" / "module2_Keyword" / "lay1.py"
    module_1_output_txt = OUTPUT_DIR_MODULE_1 / f"{input_dir_resume.stem}.txt"
    module_2_taxonomy = Path("skill_taxonomy_500plus(1).json")
    module_2_A_output_json = OUTPUT_DIR_MODULE_2_A / "layer_a_keywords.json"
    _run_module(
        module_2_A_script,
        module_1_output_txt,
        module_2_taxonomy,
        module_2_A_output_json,
    )

    module_2_B_script = PIPELINE_ROOT / "module2" / "module2_semantic" / "generate_resume_skill_json.py"
    module_2_B_output_json = OUTPUT_DIR_MODULE_2_B / "layer_a_semantic_resume.json"
    _run_module(
        module_2_B_script,
        module_1_output_txt,
        module_2_taxonomy,
        module_2_B_output_json,
    )

    module_2_combine_script = PIPELINE_ROOT / "module2" / "combine.py"
    module_2_combined_output_json = OUTPUT_DIR_MODULE_2 / "Module_2_combined.json"
    _run_module(
        module_2_combine_script,
        module_2_A_output_json,
        module_2_B_output_json,
        module_2_combined_output_json,
    )

    module_3_parser_script = PIPELINE_ROOT / "module_3_jd" / "run_jd_parser.py"
    module_3_jd_text_output = OUTPUT_DIR_MODULE_3 / "jd_resulting_text.txt"
    module_3_jd_json_output = OUTPUT_DIR_MODULE_3 / "jd_parsed_output.json"
    _run_module(
        module_3_parser_script,
        "--input",
        input_dir_job_desc,
        "--txt-out",
        module_3_jd_text_output,
        "--json-out",
        module_3_jd_json_output,
    )

    module_3_scoring_script = PIPELINE_ROOT / "module_3_jd" / "jd_req" / "run_jd_scoring_pipeline.py"
    module_3_taxonomy = PIPELINE_ROOT / "module_3_jd" / "jd_req" / "skill_taxonomy_500plus(1).json"
    module_3_keyword_json = OUTPUT_DIR_MODULE_3_KEYWORD / "layer_a_keywords.json"
    module_3_semantic_json = OUTPUT_DIR_MODULE_3_SEMANTIC / "layer_a_semantic_resume.json"
    module_3_combined_json = OUTPUT_DIR_MODULE_3_COMBINED / "layer_a_combined_scored.json"
    _run_module(
        module_3_scoring_script,
        "--jd-text",
        module_3_jd_text_output,
        "--taxonomy",
        module_3_taxonomy,
        "--keyword-json",
        module_3_keyword_json,
        "--semantic-json",
        module_3_semantic_json,
        "--combined-json",
        module_3_combined_json,
    )

    module_4_gapengine_script = PIPELINE_ROOT / "module4" / "gapengine.py"
    module_4_output_json = OUTPUT_DIR_MODULE_4 / "gapengine_output.json"
    _run_module(
        module_4_gapengine_script,
        module_2_combined_output_json,
        module_3_combined_json,
        "-o",
        module_4_output_json,
    )

    module_5_mapper_script = PIPELINE_ROOT / "module5" / "profession_mapper.py"
    module_5_dataset_json = PIPELINE_ROOT / "module5" / "profession_mapping_engine_dataset_v7.json"
    module_5_output_json = OUTPUT_DIR_MODULE_5 / "profession_mapping_output.json"
    _run_module(
        module_5_mapper_script,
        module_2_combined_output_json,
        module_5_dataset_json,
        module_5_output_json,
    )

    module_6_path_script = PIPELINE_ROOT / "module6" / "graph_info.py"
    module_6_output_json = OUTPUT_DIR_MODULE_6 / "adaptive_path_output.json"
    _run_module(
        module_6_path_script,
        module_4_output_json,
        module_5_output_json,
        module_5_dataset_json,
        module_6_output_json,
    )

    module_6_graph_browser_script = PIPELINE_ROOT / "module6" / "graph_browser.py"
    _run_module(module_6_graph_browser_script)

    module_7_resource_script = PIPELINE_ROOT / "module7" / "resource_layer.py"
    module_7_resources_json = PIPELINE_ROOT / "module7" / "resources.json"
    module_7_output_json = OUTPUT_DIR_MODULE_7 / "learning_resources_output.json"
    _run_module(
        module_7_resource_script,
        module_6_output_json,
        module_5_dataset_json,
        module_7_resources_json,
        module_7_output_json,
    )

    module_8_reasoning_script = PIPELINE_ROOT / "module8" / "reasoning_engine.py"
    module_8_output_json = OUTPUT_DIR_MODULE_8 / "reasoning_trace_output.json"
    module_8_output_txt = OUTPUT_DIR_MODULE_8 / "reasoning_trace.txt"
    _run_module(
        module_8_reasoning_script,
        module_4_output_json,
        module_5_output_json,
        module_6_output_json,
        module_8_output_json,
        "--text-out",
        module_8_output_txt,
    )


if __name__ == "__main__":
    args = _parse_args()
    run_pipeline(args.resume, args.job_desc, args.output_dir)
