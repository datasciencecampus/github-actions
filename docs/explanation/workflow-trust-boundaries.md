# Workflow Trust Boundaries

This repository uses a three-step flow to keep project-mutation privileges away from caller repositories:

1. A target repository runs a small caller workflow.
2. That caller invokes the public `add-*` reusable workflow in this repository.
3. The public reusable workflow dispatches the internal `*-impl` workflow, which is the only layer that uses project-mutation credentials.

The result is a narrow caller contract and a separate privileged implementation boundary.

## End-to-end flow

The diagram below uses the issue flow, but the same trust split applies to the pull request flow.

```mermaid
sequenceDiagram
    participant T as Target repo<br/>caller workflow
    participant P as Public reusable workflow<br/>add-issue-to-projects.yml
    participant I as Internal implementation<br/>add-issue-to-projects-impl.yml
    participant G as GitHub API<br/>Actions + GraphQL
    participant V as ProjectsV2

    T->>P: uses: datasciencecampus/github-actions/.github/workflows/add-issue-to-projects.yml@<pinned-ref>
    Note over T,P: Caller passes business inputs + router private key only
    P->>P: Validate inputs and resolve implementation ref
    P->>G: Mint router app token<br/>actions: write on github-actions
    P->>I: workflow_dispatch with repository, issue_node_id, project_field_values
    Note over P,I: Public workflow can trigger implementation but does not mutate projects
    I->>I: Validate org scope and repository ownership
    I->>G: Mint handler app token<br/>organization-projects: write
    I->>G: Resolve issue node ID and verify source repository
    I->>V: Add issue to project and set field values
```

## Trust boundaries

The main security property is that the boundary with broader privileges sits inside this repository, not in every caller repository.

```mermaid
flowchart LR
    subgraph TR[Target repository trust boundary]
        A[Caller workflow<br/>often based on test-add-issue-to-projects-reusable.yml]
        S[Available to caller<br/>PROJECT_ROUTER_BOT_PRIVATE_KEY]
    end

    subgraph GA[datasciencecampus/github-actions public boundary]
        B[add-issue-to-projects.yml<br/>public reusable workflow]
        C[Controls<br/>input validation<br/>dispatch ref resolution<br/>router token limited to actions: write]
    end

    subgraph PI[Privileged implementation boundary]
        D[add-issue-to-projects-impl.yml<br/>internal workflow_dispatch target]
        E[Protected assets<br/>PROJECT_HANDLER_BOT_PRIVATE_KEY<br/>environment: project-automation]
        F[Controls<br/>org check<br/>repository check<br/>node ID provenance check<br/>least-privilege handler token]
    end

    A --> B
    S -. used only for dispatch .-> B
    B --> D
    C --- B
    E -. not exposed to caller .-> D
    F --- D
```

## Why this reduces risk

```mermaid
flowchart TD
    A[Caller repository compromised or misconfigured] --> B{What can the caller reach?}
    B --> C[Public reusable workflow]
    C --> D[Can dispatch internal workflow]
    D --> E[Implementation re-validates org, repo, and object provenance]
    E --> F[Project mutation only if checks pass]
    B --> G[Cannot read handler private key]
    B --> H[Cannot call GraphQL project mutations directly with handler privileges]
```

In practice, this split limits damage in a few concrete ways:

- Caller repositories only hold the router credential, which is scoped to dispatching workflows in `datasciencecampus/github-actions`.
- The public reusable workflow can validate and normalize inputs before any privileged logic runs.
- The implementation workflow owns the broader handler credential inside a protected environment in this repository.
- The implementation workflow checks that the requested organization and resolved issue or pull request actually belong to the named repository before mutating projects.
- The project-mutation path is centralized, which makes auditing, rotation, and policy changes easier than spreading privileged credentials across many repositories.

## Example caller position in the flow

For demonstration, the caller workflow in a target repository can look like the test workflow pattern used here: it gathers an issue or pull request node ID, then calls the public reusable workflow. The caller does not dispatch the internal implementation directly.

```mermaid
flowchart LR
    A[Target repo event<br/>issue opened] --> B[Target repo caller workflow]
    B --> C[uses: add-issue-to-projects.yml@version-or-sha]
    C --> D[dispatches add-issue-to-projects-impl.yml@tag]
    D --> E[ProjectsV2 mutation]
```

Related references:

- [ADR-0001: Called workflow owns secret usage](ADR-0001-called-workflow-owns-secret-usage.md)
- [ADR-0002: Use workflow_dispatch instead of repository_dispatch](ADR-0002-workflow-dispatch-over-repository-dispatch.md)
- [ADR-0004: Separate reusable workflow pinning from dispatch ref](ADR-0004-separate-reusable-pinning-from-dispatch-ref.md)
- [GitHub Apps reference](../reference/github-apps.md)
