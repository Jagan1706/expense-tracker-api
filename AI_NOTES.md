# AI_NOTES.md

## 1. Which parts were AI-generated vs. written by me

I used Claude to generate the initial scaffold of this project:
- `src/main.py` — the FastAPI app and all five endpoints (add, list, filter,
  total, delete)
- `src/models.py` — the Pydantic request/response models and validation rules
- `src/storage.py` — the in-memory store with JSON file persistence
- `tests/test_api.py` — the pytest suite (14 tests)

I did not write this code from scratch myself, but I did not just copy-paste
it blindly either — I set it up, ran it, hit a real bug, and fixed it (see
below). I also read through each file to understand what it does before
submitting.

## 2. What I validated, tested, or changed, and why

- I ran `pip install -r requirements.txt` and `pytest -v` on a clean checkout
  on my own machine. On the first run, test collection failed with:
  `pydantic.errors.PydanticUserError: Error when building FieldInfo from
  annotated attribute.`
- I traced this to `src/models.py`: the field `date` was typed using
  `date` imported directly from `datetime`, so the field name and the type
  name were identical. This specific version of Pydantic couldn't resolve
  the annotation because of that name clash.
- I fixed it by changing the import to `from datetime import date as
  date_type` and updating the field annotation to `date: date_type`. After
  that fix, all 14 tests passed.
- I then ran the server locally (`uvicorn src.main:app --reload`) and
  manually tested every endpoint through the Swagger UI at `/docs`:
  added two expenses in different categories, listed all of them, filtered
  by category, checked the total endpoint gave the correct overall and
  per-category sums, deleted an expense, and confirmed deleting it a second
  time correctly returned a 404.

## 3. AI suggestions I decided not to use, and why

Of the optional bonus features listed (search, monthly summary, Swagger
docs, Docker), I kept the Swagger/OpenAPI docs, since FastAPI provides
this automatically at `/docs` with no extra code — it satisfied the "pick
at most one" bonus without adding scope. I did not add a database, Docker
support, or extra endpoints beyond what was required, since the assignment
said no database was needed and asked for at most one bonus feature.