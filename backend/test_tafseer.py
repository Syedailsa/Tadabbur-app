from tools.searchTafseer import searchTafseer
import sys
import io
# Force UTF-8 for stdout when redirected
if not sys.stdout.isatty():  # If output is being redirected
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Test 1: Semantic search only
print("\n--- Test 1: Semantic search ---")
result = searchTafseer.invoke({"args": [{"query": "Prophet Yusuf brothers threw him into well told father wolf eaten.", "limit": 3}]})
print(result)

# Test 2: Filter by surah number only
# print("\n--- Test 2: Filter by surah number ---")
# result = searchTafseer.invoke({"args": [{"surah_number": 1, "limit": 7}]})
# print(result)

# # Test 3: Combined semantic + filter
# print("\n--- Test 3: Semantic + surah filter ---")
# result = searchTafseer.invoke({"args": [{"surah_number": 2, "verse_number": 255, "query": "throne of Allah", "limit": 1}]})
# print(result)

# # Test 4: Filter by juz
# print("\n--- Test 4: Filter by juz ---")
# result = searchTafseer.invoke({"args": [{"juz": 30, "limit": 5}]})
# print(result)

# # Test 5: Empty args — should continue gracefully
# print("\n--- Test 5: No filters no query ---")
# result = searchTafseer.invoke({"args": [{"limit": 1}]})
# print(result)
