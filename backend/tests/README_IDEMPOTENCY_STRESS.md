# Idempotency Stress Tests

## Overview

Comprehensive stress tests for idempotency guarantees under extreme conditions. These tests verify that the voting system maintains data integrity and correct behavior even when subjected to:

- 1000 simultaneous identical votes
- Network retry storms
- Race conditions
- Database deadlocks
- Concurrent operations from the same voter

## Test Scenarios

### 1. `test_1000_simultaneous_identical_votes`
**Goal**: Verify that submitting the same vote 1000 times simultaneously results in only 1 vote being created.

**Test Details**:
- Submits 1000 votes with the same idempotency key simultaneously
- Uses ThreadPoolExecutor with 50 workers
- Verifies:
  - Only 1 unique vote ID exists
  - Only 1 new vote created, 999 idempotent retries
  - No duplicate votes in database
  - Performance is reasonable (< 30s total)

### 2. `test_network_retry_simulation`
**Goal**: Simulate network retries with delays to ensure idempotency works correctly.

**Test Details**:
- Simulates 50 retries with random delays (0-10ms)
- Verifies all retries return the same vote
- Only first vote is new, all others are idempotent

### 3. `test_concurrent_votes_same_voter_different_choices`
**Goal**: Test that concurrent votes from the same voter with different choices are properly rejected.

**Test Details**:
- First vote succeeds
- Second vote with different choice should raise `DuplicateVoteError`
- Verifies only 1 vote exists in database

### 4. `test_race_condition_same_idempotency_key`
**Goal**: Test race condition where multiple threads try to create vote with same idempotency key.

**Test Details**:
- 10 threads submit votes simultaneously with same idempotency key
- Verifies only 1 vote is created
- All threads should receive the same vote

### 5. `test_database_deadlock_handling`
**Goal**: Test database deadlock handling under extreme concurrency.

**Test Details**:
- 100 votes with 50 concurrent workers
- Includes retry logic for deadlocks
- Verifies:
  - High success rate (≥95%)
  - Only 1 vote in database
  - Deadlocks are handled gracefully

**Note**: Requires PostgreSQL (skipped on SQLite)

### 6. `test_idempotency_key_manipulation`
**Goal**: Test that idempotency keys cannot be manipulated to create duplicates.

**Test Details**:
- Creates vote with specific idempotency key
- Retry with same key returns existing vote
- Attempt with different key (different fingerprint) should fail with `DuplicateVoteError` (user already voted)

### 7. `test_http_status_codes_under_retry_storm`
**Goal**: Test proper HTTP status codes when API is hit with retry storm.

**Test Details**:
- Makes 20 HTTP requests rapidly
- Verifies:
  - At least one 201 (Created) status
  - All responses are 200 or 201 (success codes)
  - Only 1 vote in database

### 8. `test_performance_under_retry_storm`
**Goal**: Test performance under retry storm (1000 requests in short time).

**Test Details**:
- Submits 1000 votes and measures response times
- Verifies:
  - Average response time < 100ms
  - Max response time < 1s
  - Only 1 vote created

### 9. `test_cache_consistency_under_load`
**Goal**: Test that cache and database stay consistent under load.

**Test Details**:
- Submits 100 votes and verifies cache/database consistency each time
- Verifies:
  - Cache has idempotency key after vote
  - Database has vote with matching idempotency key
  - All votes reference the same vote ID

## Running the Tests

### Run All Stress Tests
```bash
pytest backend/tests/test_idempotency_stress.py -v
```

### Run Specific Test
```bash
pytest backend/tests/test_idempotency_stress.py::TestIdempotencyStress::test_1000_simultaneous_identical_votes -v
```

### Skip Stress Tests (for faster test runs)
```bash
pytest -m "not stress" -v
```

## Requirements

### Database
- **PostgreSQL recommended**: These tests require true concurrent writes
- **SQLite**: Tests are automatically skipped (SQLite uses file-level locking)

### Dependencies
- `pytest`
- `pytest-django`
- `pytest-asyncio` (for async tests)

## Expected Results

All tests should verify:
1. ✅ Only 1 vote counted regardless of retries
2. ✅ No duplicate votes in database
3. ✅ Proper HTTP status codes (201 for new, 200 for idempotent)
4. ✅ Performance under retry storm is acceptable
5. ✅ Cache and database remain consistent

## Performance Benchmarks

- **1000 simultaneous votes**: Should complete in < 30s
- **Average response time**: < 100ms for idempotent checks
- **Max response time**: < 1s even under extreme load
- **Success rate**: ≥95% even with database locks

## Notes

- These tests are marked with `@pytest.mark.stress` for easy filtering
- Tests automatically skip on SQLite due to concurrency limitations
- Tests use `@pytest.mark.django_db(transaction=True)` for proper transaction handling
- All tests create fresh request objects to avoid thread-safety issues

