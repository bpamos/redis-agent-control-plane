# Reusable Step Library

This directory contains reusable deployment steps that can be referenced by multiple runbooks.

## Purpose

The step library eliminates duplication across runbooks by defining common deployment steps once and referencing them everywhere. This follows the DRY (Don't Repeat Yourself) principle and makes maintenance easier.

## Directory Structure

```
steps/
  redis_enterprise/
    vm/                    # VM-specific steps
    kubernetes/            # Kubernetes-specific steps
    database/              # Database creation steps
  redis_cloud/
    aws/                   # AWS-specific steps
```

## Step Schema

Each step is defined in a YAML file with the following structure:

```yaml
step:
  id: unique_step_id
  name: "Human-readable step name"
  description: "Detailed description of what this step does"
  doc_refs:
    - path: "path/to/documentation.md"
      section: "Section heading"
  rag_assist:
    query: "RAG query for context enrichment"
    filters:
      category: operate
      product_area: redis_software
    max_results: 5
  tool: kubectl|ssh|curl|manual
  command: "Command to execute"
  validation:
    command: "Validation command"
    expect: "Expected output"
    retry: 10
    retry_delay: 5
  parameters:
    - name: parameter_name
      type: string|int|bool
      default: "default_value"
      description: "Parameter description"
```

## Parameters

Steps can be parameterized to support different configurations. Parameters are defined in the `parameters` section and can be referenced in the step using `$PARAMETER_NAME` syntax.

### Parameter Types

- `string`: Text values
- `int`: Integer values
- `bool`: Boolean values (true/false)

### Parameter Usage

In the step definition:
```yaml
command: "kubectl apply -f https://example.com/bundle.yaml -n $NAMESPACE"
parameters:
  - name: namespace
    type: string
    default: "redis"
```

In the runbook:
```yaml
steps:
  - step_ref: redis_enterprise/kubernetes/install_operator
    parameters:
      namespace: "my-namespace"
```

## Referencing Steps in Runbooks

Instead of defining steps inline, runbooks reference steps using `step_ref`:

```yaml
runbook:
  id: runbook.example
  steps:
    - step_ref: redis_enterprise/kubernetes/install_operator
      parameters:
        namespace: $NAMESPACE
    - step_ref: redis_enterprise/kubernetes/wait_operator_ready
```

## Step Resolution

The runbook loader resolves step references by:

1. Loading the step YAML file from `steps/{step_ref}.yaml`
2. Merging parameters from the runbook with step defaults
3. Building a complete `RunbookStep` object
4. Substituting parameter values in commands and validations

## Validation

Use `scripts/validate_steps.py` to validate all steps:

```bash
python scripts/validate_steps.py
```

This checks:
- Step files exist and are valid YAML
- Required fields are present
- Parameters are properly defined
- Schema is correct

## Best Practices

1. **Single Responsibility**: Each step should do one thing well
2. **Parameterization**: Make steps reusable with parameters
3. **Documentation**: Include doc_refs and rag_assist for context
4. **Validation**: Always include validation commands
5. **Idempotency**: Steps should be safe to run multiple times
6. **Error Messages**: Provide clear error messages in validations

## Example: Creating a New Step

1. Create a new YAML file in the appropriate directory:
   ```bash
   touch steps/redis_enterprise/kubernetes/my_new_step.yaml
   ```

2. Define the step with parameters:
   ```yaml
   step:
     id: my_new_step
     name: "My New Step"
     description: "Does something useful"
     tool: kubectl
     command: "kubectl apply -f $MANIFEST_URL -n $NAMESPACE"
     parameters:
       - name: manifest_url
         type: string
         default: "https://example.com/manifest.yaml"
       - name: namespace
         type: string
         default: "default"
   ```

3. Reference it in a runbook:
   ```yaml
   steps:
     - step_ref: redis_enterprise/kubernetes/my_new_step
       parameters:
         manifest_url: "https://custom.com/manifest.yaml"
         namespace: "production"
   ```

4. Validate:
   ```bash
   python scripts/validate_steps.py
   ```

