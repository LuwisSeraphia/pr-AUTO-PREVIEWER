# AI Agent Global Guidelines

## Agent Purpose

The AI agent is designed to perform pre-merge code reviews on Python pull requests in GitHub repositories.  
It should follow the instructions in `rules.md` and `skill.md` to generate structured reports for each submission.

## Global Principles

1. **Rule-Driven**
   - All review decisions must be based on rules defined in `rules.md`.
   - For new PR diffs, the agent should match changes against existing rules and flag violations or improvement suggestions.

2. **Skill Reference**
   - The agent’s behavior must follow the guidelines defined in `skill.md`, including analysis methods, output format, and report structure.

3. **Python Files Only**
   - Only `.py` files are analyzed.
   - Non-Python files may be ignored or flagged as "no review required."

4. **Incremental Learning**
   - New PR diffs may be used as input for updating rules.
   - Uncovered modification patterns should be flagged for future rule iteration.

5. **Report Generation**
   - Each PR report should include:
     - Violated rule ID and description
     - Recommended modifications or improvements
     - Affected files and lines of code
   - Reports can be JSON or Markdown for readability by humans or systems.

6. **Safety and Reliability**
   - Handle GitHub API rate limits and network timeouts gracefully.
   - Skip or log failed requests without halting the entire process.

7. **Extensibility**
   - Support dynamic updates to rules and skills.
   - Can be extended to other Python repositories or different rule sets.

## Example Behavior

- Load `skill.md` and `rules.md`.
- Parse each new PR diff.
- Check added/deleted lines against rules.
- Generate a structured report highlighting potential problems and suggested improvements.
- Save JSON reports to `PR_records/` or return them to the calling system.
