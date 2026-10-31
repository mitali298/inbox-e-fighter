#!/usr/bin/env python3
"""
Test Suite for INBOX STREET FIGHTER — Gemini AI Integration & Fallback Engine
Tests 10 diverse, contextual email scenarios to verify intelligent categorization.
"""

import json
from server import fallback_classify_email

TEST_EMAILS = [
    {
        "id": "test-1",
        "description": "College Assignment Deadline",
        "subject": "CS 182: Final Neural Network Project Due Sunday at 11:59 PM",
        "sender": "Prof. Russell <russell@cs.berkeley.edu>",
        "snippet": "Reminder that submission deadline for Project 3 is strict. No late days allowed without prior approval.",
        "expected_category": "Important",
        "expected_action": "Keep"
    },
    {
        "id": "test-2",
        "description": "Internship Interview Invitation",
        "subject": "Google Software Engineering Internship: Invitation to Technical Round 2",
        "sender": "University Recruiting <interviews@google.com>",
        "snippet": "We enjoyed our initial conversation and would like to schedule your 45-minute technical coding interview.",
        "expected_category": "Important",
        "expected_action": "Keep"
    },
    {
        "id": "test-3",
        "description": "Shopping Discount Newsletter",
        "subject": "🔥 Flash Sale: 60% off everything at Nike Outlet this weekend",
        "sender": "Nike Special Deals <promos@nike-deals.com>",
        "snippet": "Use code NIKE60 at checkout to claim discounts on running shoes and apparel.",
        "expected_category": "Promotional",
        "expected_action": "Archive"
    },
    {
        "id": "test-4",
        "description": "Social Media Notification",
        "subject": "Alex and 8 others liked your post on LinkedIn",
        "sender": "LinkedIn Notifications <notifications@linkedin.com>",
        "snippet": "Your post 'Built an AI Street Fighter game for Gmail' is trending in Web Development.",
        "expected_category": "Social",
        "expected_action": "Label"
    },
    {
        "id": "test-5",
        "description": "Phishing & Fake Wire Alert",
        "subject": "🚨 Security Lockout: $5,000 wire transfer unauthorized. Verify SSN",
        "sender": "Bank-Security-Alert <security@bank-verify-991.ru>",
        "snippet": "Your account will be suspended. Enter your debit PIN and Social Security Number to unlock.",
        "expected_category": "Spam-like",
        "expected_action": "Archive"
    },
    {
        "id": "test-6",
        "description": "Executed Apartment Lease Contract",
        "subject": "DocuSign: Please review counter-signed lease for Apartment 4B",
        "sender": "DocuSign Real Estate <dse@docusign.net>",
        "snippet": "All parties have executed the lease agreement. Attached is your official copy.",
        "expected_category": "Important",
        "expected_action": "Keep"
    },
    {
        "id": "test-7",
        "description": "Food Delivery Coupon",
        "subject": "Hungry? Here is $15 off your next DoorDash order",
        "sender": "DoorDash Offers <deals@doordash-offers.com>",
        "snippet": "Craving sushi or burgers? Apply coupon code TASTY15 for $15 off.",
        "expected_category": "Promotional",
        "expected_action": "Archive"
    },
    {
        "id": "test-8",
        "description": "Developer GitHub CI Notification",
        "subject": "❌ Build #402 Failed on branch `feat/payment-gateway`",
        "sender": "GitHub Actions <notifications@github.com>",
        "snippet": "Workflow failed at step 'Run Test Suite'. 1 error in test_stripe.py.",
        "expected_category": "Social",
        "expected_action": "Label"
    },
    {
        "id": "test-9",
        "description": "Executive Impersonation Gift Card Scam",
        "subject": "Quick wire transfer needed: Buy 10 Apple Gift Cards immediately",
        "sender": "Imposter CEO <ceo.office@mail-forwarder.co>",
        "snippet": "I am in an urgent meeting with investors. Purchase 10 x $100 Apple cards and email photos.",
        "expected_category": "Spam-like",
        "expected_action": "Archive"
    },
    {
        "id": "test-10",
        "description": "IRS Tax Refund Notification",
        "subject": "IRS Notice: Your Federal Tax Refund of $3,450 has been approved",
        "sender": "Internal Revenue Service <notices@irs.treasury.gov>",
        "snippet": "Your 2025 tax return was processed. Direct deposit of $3,450 will post in 1-2 business days.",
        "expected_category": "Important",
        "expected_action": "Keep"
    }
]

def run_tests():
    print("==========================================================")
    print("🧪 RUNNING 10 EMAIL INTELLIGENCE TESTS (FALLBACK ENGINE)")
    print("==========================================================")
    passed = 0
    for idx, test in enumerate(TEST_EMAILS, 1):
        res = fallback_classify_email(test)
        cat_match = res['category'] == test['expected_category']
        act_match = res['recommendedAction'] == test['expected_action']

        status = "✅ PASS" if (cat_match and act_match) else "❌ FAIL"
        if cat_match and act_match:
            passed += 1

        print(f"Test {idx:02d}: {test['description']:<35} -> {status}")
        print(f"         Subject: '{test['subject'][:45]}...'")
        print(f"         Result: Category={res['category']} ({res['confidenceScore']}%), Action={res['recommendedAction']}, Reply={res['requiresReply']}")
        print(f"         Reason: {res['reason']}")
        print("-" * 58)

    print(f"\nRESULTS: {passed}/{len(TEST_EMAILS)} Tests Passed ({int(passed/len(TEST_EMAILS)*100)}%)")
    assert passed == len(TEST_EMAILS), f"Expected 10/10 passed, got {passed}"
    print("✨ ALL 10 CONTEXTUAL EMAIL TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
