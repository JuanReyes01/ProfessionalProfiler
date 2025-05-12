import sys
import pandas as pd
from professional_profiler.logging.logger import get_logger, setup_logging
from professional_profiler.config import load_app_config
from professional_profiler.parsing.extract_content import (
    build_heading_tree_with_content,
    search_keywords_in_tree,
    load_html_from_df,
    extract_infobox_education,
)
from professional_profiler.parsing.section_extraction import parse_degrees_from_content

# Initialize first thing in main
setup_logging()
logger = get_logger(__name__)
config = load_app_config()


def load_keywords(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


keywords = load_keywords("./data/keywords/keywords.txt")


def handle_no_results(tree, results):

    if not results:
        # 1) run the “scan every section” fallback
        degree_sentences = handle_missing_sections(tree)
        # 2) see if our keyword list grew, and do a proper keyword‐based parse now
        new_results = search_keywords_in_tree(tree, keywords)
        if new_results:
            degree_sentences = parse_degrees_from_content(new_results)
    else:
        degree_sentences = parse_degrees_from_content(results)

    return degree_sentences


def handle_missing_sections(tree):
    all_sections = [{"id": b["id"], "title": b["title"], "content": b["content"]} for b in tree]
    # parse_degrees now returns list of (section_id, sentence) pairs
    hits = []
    for sec in all_sections:
        for sent in parse_degrees_from_content([sec]):
            hits.append((sec["id"], sec["title"], sent))

    # add each unique section-title that produced ≥1 hit
    new_titles = {title for (_id, title, _s) in hits}
    for title in new_titles:
        if title not in keywords:
            keywords.append(title)
            print(f"Added keyword from section: {title}")

    # return just the extracted sentences
    return [s for (_id, _t, s) in hits]


def save_keywords(path, keywords):
    # dedupe and sort
    unique = sorted(set(keywords), key=keywords.index)
    with open(path, "w", encoding="utf-8") as f:
        for kw in unique:
            f.write(kw + "\n")


# ===== MAIN =====


def main():
    logger.info("Starting parsing")
    # Load the configuration
    logger.debug("Configuration loaded: %s", config)
    # Load the dataset
    dataset_path = config.scraping.paths.processed_data + config.scraping.file.name

    db = pd.read_csv(dataset_path)
    logger.info("Loading HTML from DataFrame")
    db["html"] = db["source"].apply(load_html_from_df)

    logger.info("Creating heading tree")
    db["tree"] = db["html"].apply(build_heading_tree_with_content)
    logger.info("Extracting infobox education")
    db["infobox_education"] = db["html"].apply(extract_infobox_education)
    logger.info("Searching keywords in tree")
    db["search_results"] = db["tree"].apply(lambda t: search_keywords_in_tree(t, keywords))

    logger.info("Starting content parsing")
    db["degree_sentences"] = db.apply(
        lambda row: handle_no_results(row["tree"], row["search_results"]), axis=1
    )
    save_keywords("./data/keywords/keywords.txt", keywords)
    db["degree_sentences"] = db.apply(
        lambda row: row["degree_sentences"]
        + ([row["infobox_education"]] if row["infobox_education"] else []),
        axis=1,
    )

    # Create a new df with just the name of the person and the degree sentences
    final = db[["id", "author_name", "degree_sentences"]].copy()
    # save
    final.to_csv(config.parsing.results_path + config.parsing.file_name, index=False)
    logger.info("Parsing completed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger = get_logger(__name__)
        logger.exception("Fatal error in parsing")
        sys.exit(1)
