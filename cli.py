import sys
from prep_agent.agent import run

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python cli.py <company_url> [profile.pdf]")
        sys.exit(1)
    company_url = sys.argv[1]
    profile = sys.argv[2] if len(sys.argv) > 2 else "my_profile.pdf"
    run(company_url, profile)
