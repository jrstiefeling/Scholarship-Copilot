"""
draft_all.py — generates essay drafts for all scholarships in the tracker.
Run: python3 src/draft_all.py
"""
import os, sys, time
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from drafter import draft

SCHOLARSHIPS = [
    {
        "name": "Inland Ivy Foundation",
        "prompt": "Tell us about yourself, your academic achievements, and your goals for the future. How have you contributed to your school or community in the Inland Empire?",
        "word_limit": 500,
    },
    {
        "name": "Inland Empire Community Foundation (IECF)",
        "prompt": "Describe a meaningful experience that has shaped who you are and how it connects to your future goals. How have you made a positive impact in your community?",
        "word_limit": 650,
    },
    {
        "name": "Inland Empire Cash for College",
        "prompt": "What are your educational and career goals, and how will attending college help you achieve them? How has your background and community shaped your aspirations?",
        "word_limit": 500,
    },
    {
        "name": "Miracles and Dreams Foundation",
        "prompt": "What is your dream, and what steps have you taken to pursue it? Describe how your experiences in the Inland Empire community have influenced your vision for the future.",
        "word_limit": 600,
    },
    {
        "name": "Tencent America Scholarship",
        "prompt": "Describe your academic and extracurricular achievements and how they reflect your commitment to your community and future career. What impact do you hope to make in your field?",
        "word_limit": 600,
    },
    {
        "name": "College Pathways Scholarship",
        "prompt": "Why have you chosen your intended career path, and how have your high school experiences prepared you to pursue it? Describe any relevant activities, service, or leadership that demonstrate your commitment.",
        "word_limit": 500,
    },
    {
        "name": "Cameron Impact Scholarship",
        "prompt": "Describe a significant challenge you have faced and how you overcame it. What does leadership mean to you, and how have you demonstrated it in your school or community? What impact do you intend to make in the world?",
        "word_limit": 650,
    },
    {
        "name": "Bold.org $2,000 Monthly Scholarship",
        "prompt": "Tell us about yourself: your goals, passions, and what motivates you to pursue higher education. What makes you stand out as a student and community member?",
        "word_limit": 400,
    },
    {
        "name": "Bold.org High School Scholarship",
        "prompt": "What are you most passionate about, and how has that passion shaped your high school experience and your plans for the future?",
        "word_limit": 400,
    },
    {
        "name": "Scholarships360 $10,000 No-Essay Scholarship",
        "prompt": "Describe your academic journey, your involvement in your school and community, and your goals for college and beyond. Why do you deserve this scholarship?",
        "word_limit": 500,
    },
    {
        "name": "California Scholarship Federation (CSF)",
        "prompt": "As a CSF member, you have demonstrated academic excellence and commitment to service. Describe how scholarship and service have shaped your high school experience and what you hope to contribute to your college community and beyond.",
        "word_limit": 500,
    },
    {
        "name": "Jack Kent Cooke Young Scholars",
        "prompt": "Describe your intellectual passions and academic interests. What drives your curiosity and love of learning? How have you pursued these interests outside the classroom, and how do they connect to your future goals?",
        "word_limit": 650,
    },
    {
        "name": "Coca-Cola Scholars Program",
        "prompt": "Describe your leadership experiences and how you have served your community. What have you learned about yourself through these experiences, and how will you continue to lead and give back in college and beyond?",
        "word_limit": 650,
    },
    {
        "name": "US Senate Youth Program",
        "prompt": "What does civic engagement and public service mean to you? Describe an experience where you worked to make a positive change in your school or community. How has this shaped your understanding of democracy and your role as a citizen?",
        "word_limit": 600,
    },
    {
        "name": "Ontario-Montclair Promise Scholars",
        "prompt": "How has growing up in the Inland Empire shaped your identity and aspirations? Describe your involvement in your school and community, and explain how this scholarship will help you pursue your educational goals.",
        "word_limit": 500,
    },
]

if __name__ == "__main__":
    total = len(SCHOLARSHIPS)
    succeeded = []
    failed = []

    print(f"Drafting essays for {total} scholarships...\n{'='*60}\n")

    for i, s in enumerate(SCHOLARSHIPS, 1):
        print(f"[{i}/{total}] {s['name']}")
        try:
            url = draft(s["name"], s["prompt"], s["word_limit"])
            succeeded.append((s["name"], url))
            print(f"  ✓ Done\n")
        except Exception as e:
            print(f"  ✗ Failed: {e}\n")
            failed.append((s["name"], str(e)))
        if i < total:
            time.sleep(2)  # avoid rate limiting

    print(f"\n{'='*60}")
    print(f"COMPLETE: {len(succeeded)}/{total} essays drafted\n")
    for name, url in succeeded:
        print(f"  ✓ {name}")
        print(f"    {url}")
    if failed:
        print(f"\nFailed ({len(failed)}):")
        for name, err in failed:
            print(f"  ✗ {name}: {err}")
