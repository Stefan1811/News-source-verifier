import re
import json
import csv
import os
from aop_wrapper import Aspect

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


