---
description: Testing guidance; attach when the user asks to write/add tests, test components,  create test cases, or similar testing-related requests.
alwaysApply: false
---

## ⚠️ CRITICAL FIRST STEP - Prerequisites Before Writing Tests

### 1. Test Case Requirements
**MANDATORY: You MUST follow this process before writing ANY tests.**

**Required Process:**
1. **ALWAYS start with confirmation, even if user provides test cases:**
   - **Step 1**: List all provided test cases back to user for confirmation
   - **Step 2**: Review and validate the quality of each test case
   - **Step 3**: Suggest improvements if cases are unclear or incomplete
   - **Step 4**: Ask user: "Please confirm these test cases are correct, or provide any modifications:"
   - **Step 5**: Wait for user confirmation before proceeding
   - **Step 6**: Only start writing tests after user explicitly confirms

2. **If user does NOT provide test cases:**
   - Ask user to provide specific test cases for the component/functionality
   - Do NOT write any tests until test cases are provided
   - Do NOT make assumptions about what should be tested

**CRITICAL**: Never skip the confirmation step, even if test cases seem clear and complete.

### 2. Test-Driven Development (TDD) Approach
- **Destination**: Test code (what you're writing)
- **Source**: Code being tested (existing implementation)
- **Process**: 
  1. Write test first based on user's test cases
  2. If test fails, intelligently fix either the source code or test code
  3. Make tests pass by updating implementation or correcting test logic
  4. Focus ONLY on user-provided test cases, ignore existing source code assumptions

## Test File Organization

### Simple Component Structure
**Definition**: Component with single file, no sub-components, no helpers/hooks

**File Structure:**
```
ComponentName/
├── ComponentName.tsx
├── ComponentName.types.ts (if exists)
├── index.ts
└── ComponentName.test.tsx  # Test file in same directory
```

**Example:**
```
ActionButton/
├── ActionButton.tsx
├── ActionButton.types.ts
├── index.ts
└── ActionButton.test.tsx
```

### Complex Component Structure
**Definition**: Component with multiple sub-components, helpers, hooks, or nested folders

**File Structure:**
```
ComponentName/
├── ComponentName.tsx
├── ComponentName.types.ts
├── index.ts
├── __tests__/                    # Dedicated tests folder
│   ├── ComponentName.test.tsx
│   ├── SubComponent.test.tsx
│   ├── helpers.test.ts
│   └── hooks.test.ts
├── components/
│   └── SubComponent.tsx
├── helpers.ts
└── hooks/
    └── useCustomHook.ts
```

**Example:**
```
SidebarSection/
├── SidebarSection.tsx
├── SidebarSection.types.ts
├── index.ts
├── __tests__/
│   ├── SidebarSection.test.tsx
│   ├── Handlebar.test.tsx
│   └── useDragToScroll.test.ts
├── Handlebar/
│   ├── Handlebar.tsx
│   └── index.ts
└── hooks/
    └── useDragToScroll.ts
```

## Mocking Guidelines

### 1. Mock Data Location
- **Primary location**: `src/tests/__mocks__/`
- **Search existing mocks first** before creating new ones
- **Reuse existing mocks** whenever possible

### 2. Mock Creation Rules
- **Keep mocks simple** - avoid over-complicating due to TypeScript issues
- **Mock only consumed properties** - only mock object keys that are actually used in the source code
- **Bypass TypeScript if needed** - use `any` type or type assertions when necessary for simplicity

### 3. Mock Cleanup
- **Smart use of beforeEach**: Use beforeEach() only when needed.
- **Clear mocks after all tests**: Use `afterAll()` to clean up mock state
- **Example:**
```typescript
afterAll(() => {
  jest.resetAllMocks();
});
```

## DOM Element Selection Strategy

### Priority Order for Element Selection:
1. **First Priority**: Select elements by `data-testid` attribute
2. **Second Priority**: Select elements by `id` attribute
3. **Third Priority**: Select elements by `className` or other attributes
4. **Last Resort**: Use complex selectors (avoid when possible)

### Adding Test IDs:
- If elements don't have test IDs, add `data-testid` attributes to the source code
- Use descriptive test IDs: `data-testid="submit-button"` not `data-testid="btn"`

## Test Execution

### Running Tests
**Command**: `yarn test <filepath>`
**Location**: Run from `src/` directory

**Examples:**
```bash
# From src/ directory
yarn test src/shared/components/ActionButton/ActionButton.test.tsx
yarn test src/components/SidebarSection/__tests__/SidebarSection.test.tsx
```

### Test File Naming Convention
- **Simple components**: `ComponentName.test.tsx` (in same directory)
- **Complex components**: `ComponentName.test.tsx` (in `__tests__/` folder)

## Quality Assurance

### Self-Review Checklist
Before completing tests, review and remove:
- [ ] Unnecessary mock setups
- [ ] Redundant test cases not requested by user
- [ ] Unused imports or variables
- [ ] Overly complex test logic
- [ ] Tests that don't match user's provided test cases

### Test Quality Standards
- **Focus**: Only test what user specifically requested
- **Clarity**: Test descriptions should clearly indicate what is being tested
- **Independence**: Each test should be independent and not rely on other tests
- **Simplicity**: Keep tests simple and readable. Do not overcomplicate tests.

## Common Anti-Patterns to Avoid

1. **Writing tests without user-provided cases**
2. **Making assumptions about what should be tested**
3. **Over-mocking or creating complex mock structures**
4. **Writing tests that don't match user's requirements**
5. **Not cleaning up mocks between tests**
6. **Using complex DOM selectors when simple ones work**
7. **Writing tests for functionality not requested by user**


## Self review tests before verdict
- After iteratively fixing test cases, before winding up tests, Do a self code review of quality of tests. Remove any unnecessary mocks/tests/any other code block.
