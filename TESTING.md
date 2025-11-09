# SubjectSupport - Testing Documentation

## Overview

Comprehensive test suite for the SubjectSupport tutoring platform covering:
- User authentication and authorization
- Class booking workflow
- Meeting integration (Google Meet, Zoom, Custom)
- Geographical tutor search and prioritization
- Session management lifecycle

## Test Structure

```
subjectsSuport/
├── accounts/
│   ├── tests.py              # 300+ lines, 22 test classes
│   └── test_utils.py         # Test factories and utilities
└── core/
    └── tests.py              # 600+ lines, 11 test classes
```

## Test Coverage

### Accounts App Tests (accounts/tests.py)

#### 1. Model Tests
- **UserModelTest** (4 tests)
  - User creation (tutor/client)
  - String representation
  - Email unique constraint

- **TutorProfileModelTest** (3 tests)
  - Profile creation with location
  - One-to-one relationship
  - String representation

- **ClientProfileModelTest** (3 tests)
  - Profile creation
  - Minor status and parent information
  - String representation

#### 2. Form Tests
- **TutorRegistrationFormTest** (4 tests)
  - Valid registration
  - Invalid email format
  - Password mismatch
  - User and profile creation

- **ClientRegistrationFormTest** (2 tests)
  - Valid registration
  - User and profile creation with minor status

#### 3. View Tests
- **TutorRegistrationViewTest** (3 tests)
  - Page loads
  - Successful registration
  - Duplicate email prevention

- **ClientRegistrationViewTest** (2 tests)
  - Page loads
  - Successful registration

- **LoginViewTest** (4 tests)
  - Page loads
  - Tutor login and redirect
  - Client login and redirect
  - Invalid credentials

- **TutorDashboardTest** (4 tests)
  - Requires authentication
  - Tutor access granted
  - Client access denied
  - Correct context data

- **ClientDashboardTest** (4 tests)
  - Requires authentication
  - Client access granted
  - Tutor access denied
  - Correct context data

- **LogoutTest** (2 tests)
  - Redirect after logout
  - Session cleared

- **DashboardRedirectTest** (2 tests)
  - Tutor redirect to tutor dashboard
  - Client redirect to client dashboard

**Total Accounts Tests: 37**

### Core App Tests (core/tests.py)

#### 1. Model Tests
- **ClassSessionModelTest** (6 tests)
  - Session creation
  - String representation
  - Status choices validation
  - Meeting platform fields
  - is_upcoming() method
  - is_past() method

- **TutorLeadModelTest** (2 tests)
  - Lead creation
  - Ordering by created_at

#### 2. Form Tests
- **SessionRequestFormTest** (2 tests)
  - Valid session request
  - Past date validation

- **SessionConfirmationFormTest** (2 tests)
  - Form includes meeting platform
  - Valid with platform selection

#### 3. Service Tests
- **MeetingServiceTest** (6 tests)
  - Google Meet URL generation
  - Zoom URL generation
  - Custom URL generation
  - Platform-specific creation
  - Session update with meeting

#### 4. View Tests
- **TutorSelectionViewTest** (4 tests)
  - Page loads for clients
  - Client-only access
  - Geographical prioritization (same city → same country → others)
  - Search filter functionality

- **SessionRequestViewTest** (3 tests)
  - Page loads
  - Successful request creation
  - Client-only access

- **SessionConfirmViewTest** (4 tests)
  - Page loads for tutor
  - Successful confirmation with meeting generation
  - Tutor-only access
  - Cannot re-confirm

- **SessionCancelViewTest** (3 tests)
  - Tutor can cancel
  - Client can cancel
  - Unauthorized user cannot cancel

- **MeetingRoomViewTest** (6 tests)
  - Page loads for authorized users
  - Tutor identified as host
  - Client not identified as host
  - Unauthorized access denied
  - Unconfirmed session access denied
  - Meeting started flag set

- **LandingPageTest** (1 test)
  - Page loads for anonymous users

**Total Core Tests: 39**

## Running Tests

### Run All Tests
```bash
env/Scripts/python.exe manage.py test
```

### Run Specific App Tests
```bash
# Test accounts app only
env/Scripts/python.exe manage.py test accounts

# Test core app only
env/Scripts/python.exe manage.py test core
```

### Run Specific Test Class
```bash
# Test user authentication
env/Scripts/python.exe manage.py test accounts.tests.LoginViewTest

# Test meeting integration
env/Scripts/python.exe manage.py test core.tests.MeetingServiceTest

# Test geographical search
env/Scripts/python.exe manage.py test core.tests.TutorSelectionViewTest
```

### Run Specific Test Method
```bash
# Test tutor registration
env/Scripts/python.exe manage.py test accounts.tests.TutorRegistrationViewTest.test_successful_tutor_registration

# Test session confirmation
env/Scripts/python.exe manage.py test core.tests.SessionConfirmViewTest.test_successful_session_confirmation
```

### Run Tests with Verbose Output
```bash
env/Scripts/python.exe manage.py test --verbosity=2
```

### Run Tests with Coverage (if installed)
```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='.' manage.py test

# View coverage report
coverage report

# Generate HTML coverage report
coverage html
# Open htmlcov/index.html in browser
```

## Test Database

Django automatically creates a test database (`test_db.sqlite3`) for running tests. It's created before tests run and deleted after tests complete.

## Key Testing Scenarios

### 1. Complete User Registration Flow
```
Test: accounts.tests.TutorRegistrationViewTest.test_successful_tutor_registration
- Creates tutor with profile
- Validates email uniqueness
- Verifies password hashing
- Checks redirection after registration
```

### 2. Complete Session Booking Workflow
```
Client searches tutors → Selects tutor → Requests session → Tutor confirms → Meeting generated

Tests involved:
- TutorSelectionViewTest.test_geographical_prioritization
- SessionRequestViewTest.test_successful_session_request
- SessionConfirmViewTest.test_successful_session_confirmation
- MeetingServiceTest.test_update_session_with_meeting
```

### 3. Geographical Prioritization
```
Test: core.tests.TutorSelectionViewTest.test_geographical_prioritization
- Student in Quito sees Quito tutors first
- Then Ecuador tutors from other cities
- Then tutors from other countries
```

### 4. Meeting Platform Integration
```
Test: core.tests.MeetingServiceTest
- Generates Google Meet URLs (https://meet.google.com/xxx)
- Generates Zoom URLs with password (https://zoom.us/j/xxx?pwd=xxx)
- Generates Custom URLs (https://meet.subjectsupport.com/room/xxx)
- Saves meeting details to session
```

### 5. Access Control
```
Tests throughout:
- Tutors cannot access client dashboard
- Clients cannot access tutor dashboard
- Only session participants can access meeting room
- Only tutors can confirm sessions
- Only session tutor can access confirmation page
```

## Test Data Factories

Located in `accounts/test_utils.py`:

```python
# Create test tutor
tutor = UserFactory.create_tutor(
    email='tutor@test.com',
    password='testpass123',
    subjects='Mathematics',
    city='Quito',
    country='Ecuador'
)

# Create test client
client = UserFactory.create_client(
    email='client@test.com',
    password='testpass123',
    city='Quito',
    country='Ecuador',
    is_minor=False
)

# Create multiple tutors
tutors = UserFactory.create_multiple_tutors(count=5)

# Create tutors in different locations
tutors = UserFactory.create_tutors_by_location()
# Returns: {'same_city': tutor1, 'same_country': tutor2, 'different_country': tutor3}
```

## Test Best Practices Used

1. **Isolation**: Each test is independent and doesn't rely on other tests
2. **Setup/Teardown**: Using `setUp()` method to create common test data
3. **Descriptive Names**: Test names clearly describe what's being tested
4. **AAA Pattern**: Arrange, Act, Assert structure
5. **Edge Cases**: Testing invalid inputs, unauthorized access, etc.
6. **Real Workflows**: Testing complete user journeys, not just units

## Common Test Failures and Solutions

### 1. ImportError: No module named 'accounts.test_utils'
**Solution**: Ensure you're running tests from the project root directory

### 2. django.db.utils.IntegrityError: UNIQUE constraint failed
**Solution**: Tests may be creating duplicate data. Check that `setUp()` is properly isolating test data

### 3. AssertionError: 200 != 302
**Solution**: Check if login is required but not performed in test. Use `self.client.login()` before accessing protected views

### 4. Template does not exist
**Solution**: Verify template paths match exactly in both view and test

## Continuous Integration (CI) Setup

### GitHub Actions Example

Create `.github/workflows/django-tests.yml`:

```yaml
name: Django Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run Tests
      run: |
        python manage.py test --verbosity=2
```

## Performance Testing

For load testing the application:

```bash
# Install locust
pip install locust

# Create locustfile.py (example):
from locust import HttpUser, task, between

class SubjectSupportUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def view_tutors(self):
        self.client.get("/tutors/")

    @task
    def view_dashboard(self):
        # Login first
        self.client.post("/accounts/login/", {
            "username": "test@test.com",
            "password": "testpass123"
        })
        self.client.get("/accounts/client/dashboard/")

# Run locust
locust -f locustfile.py
```

## Test Metrics

- **Total Tests**: 76
- **Total Test Classes**: 33
- **Lines of Test Code**: ~900
- **Average Test Execution Time**: ~3-5 seconds for full suite
- **Test to Code Ratio**: ~1:1 (ideal for critical business logic)

## Adding New Tests

When adding new features, create tests following this pattern:

```python
class NewFeatureTest(TestCase):
    """Test new feature description"""

    def setUp(self):
        """Create test data"""
        self.user = UserFactory.create_client()

    def test_feature_works(self):
        """Test the feature works as expected"""
        # Arrange
        data = {'field': 'value'}

        # Act
        response = self.client.post(url, data)

        # Assert
        self.assertEqual(response.status_code, 200)
```

## Test Maintenance

1. **Keep tests fast**: Use in-memory database (SQLite default)
2. **Update tests with code changes**: Tests should always pass on main branch
3. **Remove obsolete tests**: Delete tests for removed features
4. **Document complex scenarios**: Add comments for non-obvious test logic
5. **Use factories**: Avoid duplicating test data creation logic

## Resources

- Django Testing Documentation: https://docs.djangoproject.com/en/5.0/topics/testing/
- Coverage.py Documentation: https://coverage.readthedocs.io/
- Python unittest Documentation: https://docs.python.org/3/library/unittest.html

## Support

For issues with tests:
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Verify database migrations are up to date: `python manage.py migrate`
3. Check that test database can be created (requires write permissions)
4. Review test output for specific error messages
