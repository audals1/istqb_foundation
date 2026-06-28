"""ISTQB Sample Exam PDF parser note.

This MVP package stores parsed JSON under data/.
For future versions, reuse the parsing logic from update_istqb_mvp_b.py / build_istqb_mvp.py:
1. Extract questions by expected question number order.
2. Extract answer key from the summary table.
3. Extract explanations by question number and LO boundary.
4. Render figure/table-heavy pages as PNG assets.
5. Validate count, choices, answers, explanations, and visual assets.
"""
print("Use the parser/build script bundled in tools/ as the current reference implementation.")
