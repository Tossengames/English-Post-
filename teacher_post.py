import random
import requests
import json
import re
import os
from datetime import datetime

# ===== CONFIGURATION =====
FB_PAGE_TOKEN = os.getenv('FB_PAGE_TOKEN')       # Your Facebook Page Token
FB_PAGE_ID = os.getenv('FB_PAGE_ID')             # Your Facebook Page ID
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')     # Your Gemini API Key
PIXABAY_KEY = os.getenv('PIXABAY_KEY')           # Your Pixabay API Key

# ===== IMAGE KEYWORDS =====
PIXABAY_KEYWORDS = [
    "learning", "education", "books", "study", "classroom",
    "language", "writing", "reading", "students", "teacher",
    "notebook", "pen", "laptop", "online", "school"
]

# ===== UPDATED ENGLISH TEACHING & LANGUAGE LEARNING TOPICS =====
LESSON_TOPICS = [
    # 🆕 MODERN TEACHING METHODS (20 topics)
    "🚀 Gamification in English Learning",
    "💡 Micro-learning: 5-Minute Daily Practice",
    "🎯 Task-Based Language Teaching",
    "🤖 AI Tools for English Practice",
    "📱 Best Apps for Language Learning",
    "🎧 Learn English Through Podcasts",
    "📺 Using YouTube for English Improvement",
    "🗣️ Conversation Clubs Benefits",
    "📝 Error Correction Techniques",
    "🧠 Memory Techniques for Vocabulary",
    "🎮 Language Learning Games",
    "📚 Extensive Reading Approach",
    "🎵 Learn English Through Music",
    "💬 Chatting with Native Speakers",
    "📊 Progress Tracking Methods",
    "⏰ Time Management for Learners",
    "🎯 Goal Setting in Language Learning",
    "🔄 Spaced Repetition Systems",
    "📖 Graded Readers Strategy",
    "🎭 Role-Play Activities",

    # 🆕 LANGUAGE SKILLS FOCUS (25 topics)
    "🗣️ Shadowing Technique for Pronunciation",
    "👂 Active Listening Practice",
    "📖 Speed Reading in English",
    "✍️ Journaling for Fluency",
    "🎤 Public Speaking Practice",
    "📧 Business Email Writing",
    "💼 Professional Presentation Skills",
    "🤝 Small Talk Strategies",
    "📋 Note-Taking in English",
    "🔊 Voice Recording for Self-Correction",
    "📖 Context Clues for Vocabulary",
    "🗂️ Word Mapping Techniques",
    "🔤 Root Words and Affixes",
    "🎯 Idioms in Context Learning",
    "🔄 Phrasal Verbs Made Easy",
    "📝 Paragraph Structure Basics",
    "🎭 Tone and Register Awareness",
    "🔍 Skimming and Scanning Skills