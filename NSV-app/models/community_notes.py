import re
import json
import csv
import mop
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.aop_wrapper import Aspect

@Aspect.log_execution
@Aspect.measure_time
@Aspect.handle_exceptions
def extract_tweet_id(tweet_url):
    """
    Extract the tweet ID from a Twitter URL.
    """
    match = re.search(r"/status/(\d+)", tweet_url)
    return match.group(1) if match else None

@Aspect.log_execution
@Aspect.measure_time
@Aspect.handle_exceptions
def get_tweet_info_from_notes(tweet_id, file_name="notes.tsv"):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "..", file_name)

    print(f"Looking for file at: {file_path}")  # Debugging
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter="\t")
        for row in reader:
            if row["tweetId"] == tweet_id:
                return {
                    "noteId": row.get("noteId", "N/A"),
                    "noteAuthorParticipantId": row.get("noteAuthorParticipantId", "N/A"),
                    "createdAtMillis": row.get("createdAtMillis", "N/A"),
                    "tweetId": row.get("tweetId", "N/A"),
                    "classification": row.get("classification", "N/A"),
                    "believable": row.get("believable", "N/A"),
                    "harmful": row.get("harmful", "N/A"),
                    "validationDifficulty": row.get("validationDifficulty", "N/A"),
                    "misleadingOther": row.get("misleadingOther", "N/A"),
                    "misleadingFactualError": row.get("misleadingFactualError", "N/A"),
                    "misleadingManipulatedMedia": row.get("misleadingManipulatedMedia", "N/A"),
                    "misleadingOutdatedInformation": row.get("misleadingOutdatedInformation", "N/A"),
                    "misleadingMissingImportantContext": row.get("misleadingMissingImportantContext", "N/A"),
                    "misleadingUnverifiedClaimAsFact": row.get("misleadingUnverifiedClaimAsFact", "N/A"),
                    "misleadingSatire": row.get("misleadingSatire", "N/A"),
                    "notMisleadingOther": row.get("notMisleadingOther", "N/A"),
                    "notMisleadingFactuallyCorrect": row.get("notMisleadingFactuallyCorrect", "N/A"),
                    "notMisleadingOutdatedButNotWhenWritten": row.get("notMisleadingOutdatedButNotWhenWritten", "N/A"),
                    "notMisleadingClearlySatire": row.get("notMisleadingClearlySatire", "N/A"),
                    "notMisleadingPersonalOpinion": row.get("notMisleadingPersonalOpinion", "N/A"),
                    "trustworthySources": row.get("trustworthySources", "N/A"),
                    "summary": row.get("summary", "N/A"),
                    "isMediaNote": row.get("isMediaNote", "N/A"),
                }
    return None


#@mop.monitor(
  #  lambda file_name: isinstance(file_name, str) and os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", file_name)),
  #  lambda file_name: f"File {file_name} does not exist or invalid file path."
#)
@Aspect.log_execution
@Aspect.measure_time
@Aspect.handle_exceptions
def validate_tsv(file_name="notes.tsv"):
    try:
        print("Executing VALIDATE")

        official_columns = [
            "noteId", "noteAuthorParticipantId", "createdAtMillis", "tweetId", "classification",
            "believable", "harmful", "validationDifficulty", "misleadingOther", "misleadingFactualError",
            "misleadingManipulatedMedia", "misleadingOutdatedInformation", "misleadingMissingImportantContext",
            "misleadingUnverifiedClaimAsFact", "misleadingSatire", "notMisleadingOther",
            "notMisleadingFactuallyCorrect", "notMisleadingOutdatedButNotWhenWritten",
            "notMisleadingClearlySatire", "notMisleadingPersonalOpinion", "trustworthySources",
            "summary", "isMediaNote"
        ]
        valid_classifications = ["NOT_MISLEADING", "MISINFORMED_OR_POTENTIALLY_MISLEADING"]

        with open(file_name, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter="\t")
            if set(reader.fieldnames) != set(official_columns):
                print("Error: File does not contain the required columns.")
                return False

            for row in reader:
                if row["classification"] not in valid_classifications:
                    print(f"Error: Invalid classification in row: {row}")
                    return False

        print("Validation PASSED")
        return True
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False



@mop.monitor(
    lambda file_name: file_name and isinstance(file_name, str) and os.path.exists(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", file_name)
    ),
    lambda file_name: f"File {file_name} does not exist or invalid file path."
)

@Aspect.log_execution
@Aspect.measure_time
@Aspect.handle_exceptions
def clean_tsv(file_name="notes.tsv", valid_classifications=None):
    """
    Clean the TSV file by removing invalid rows.
    """
    print("Executing CLEAN")

    if valid_classifications is None:
        valid_classifications = ["NOT_MISLEADING", "MISINFORMED_OR_POTENTIALLY_MISLEADING"]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "..", file_name)

    cleaned_rows = []
    print(f"Cleaning file at: {file_path}")
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter="\t")

        # Selectăm doar rândurile valide
        for row in reader:
            if row["classification"] in valid_classifications:
                cleaned_rows.append(row)

    # Scrierea datelor curățate înapoi în fișier
    with open(file_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=reader.fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(cleaned_rows)

    print(f"Cleaned file successfully. Total valid rows: {len(cleaned_rows)}")

#if __name__ == "__main__":
#    tsv_file = "notes.tsv"
#    if validate_tsv(tsv_file):
#        print("File validation successful.")
#    else:
#        print("File validation failed.")
#
#    clean_tsv(tsv_file)
