# okrapdf CLI reference

All commands are `npx okrapdf@latest <command>`. Use `--json` in agent workflows.

## Dashboard

```bash
npx okrapdf@latest [file.pdf]
```

| Flag | Effect |
| --- | --- |
| `--background` | Start the server, print the URL, and return. It stops after 30 idle minutes. |
| `--json` | Print `{"url","documentId","reused","pid"}`. |
| `--port <n>` | First port to try. The default is 7373, and it moves up if the port is in use. |
| `--no-open` | Do not open a browser. |

With a dashboard running, this command adds the file to it and sets `reused` to `true`.

## Models

```bash
npx okrapdf@latest model --json
```

| Field | Meaning |
| --- | --- |
| `models[].id` | The value for `--model`. |
| `models[].kind` | `builtin`, `local`, `byok`, or `custom`. |
| `models[].vision` | `true`, `false`, or `null` when the server does not report it. |
| `local[]` | Each server with `state` (`running`, `installed`, `absent`) and a `hint`. |
| `byok[]` | Each provider with `configured` and `keySource` (`env`, `saved`, `session`). No key value appears here. |
| `host` | CPU, memory, and whether `uv` exists. |
| `recommendations[]` | Models that fit this computer, with the `ollama pull` command. |

## Parse

```bash
npx okrapdf@latest parse <file.pdf> [--model <id>] [--pages 1-3,7] [--json] [--output <file>]
```

The default model is `builtin/text-layer`. The default output is markdown. The command exits non-zero if a page fails.

## Bench

```bash
npx okrapdf@latest bench --model <id> [--full] [--json]
```

This command parses ParseBench pages, then runs the published `parse-bench` evaluator through `uvx`. The default is the 12-page test set. `--full` is the 2,000-page dataset. Files go to `~/.cache/okrapdf/parsebench/`.

## Selection

```bash
npx okrapdf@latest context
```

Prints `{"selection":{"documentId","runId","blockId","page","label","bbox","text","selectedAt"}}`, or `{"selection":null}`.

## Server

```bash
npx okrapdf@latest status --json
npx okrapdf@latest stop
```

## HTTP routes

The page uses these routes, and an agent can use them too. Each route is on the URL from `status`.

| Route | Purpose |
| --- | --- |
| `GET /api/state` | Documents, runs, bench runs, and the selection. |
| `GET /api/events` | Server-sent events for changes to that state. |
| `GET /api/models` | The same data as `model --json`. |
| `POST /api/runs` | Start a run: `{"documentId","modelId","pages":[1,2]}`. Omit `pages` for all pages. |
| `GET /api/runs/:id` | One run. |
| `GET /api/runs/:id/export?format=markdown` | Markdown or JSON. |

The server refuses a request with a foreign `Host` or `Origin`.
