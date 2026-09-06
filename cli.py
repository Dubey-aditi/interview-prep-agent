import sys
from prep_agent.agent import run
import argparse
from dotenv import load_dotenv


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Interview Prep Agent CLI")
    parser.add_argument(
        "company_url", type=str, help="URL of the company to prepare for"
    )
    parser.add_argument(
        "--profile",
        "-p",
        type=str,
        default="my_profile.pdf",
        help="Path to your profile markdown file",
    )
    parser.add_argument(
        "--email", type=str, default=None, help="Your email address (optional)"
    )
    args = parser.parse_args()
    run(args.company_url, args.profile, args.email)


if __name__ == "__main__":
    main()
