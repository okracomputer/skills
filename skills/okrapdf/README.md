# okraPDF dashboard

Open a local PDF parser dashboard with one command. It needs no account.

```bash
npx okrapdf report.pdf
```

![okraPDF dashboard: a hover on a PDF box finds its parsed block, and a hover on a block finds its box](../../assets/okrapdf-dashboard.gif)

<sub>Netflix Q3 2025 shareholder letter, [Form 8-K, Exhibit 99.1](https://www.sec.gov/Archives/edgar/data/1065280/000106528025000404/ex991_q325.htm), parsed with Gemini 3 Flash. okraPDF has no connection with Netflix.</sub>

- **Side by side:** the PDF is on the left, and the parsed blocks are on the right. A hover on either side highlights the other. A block on another page moves the PDF to its source.
- **Charts:** a vision model reads a chart into a data table, and the hover maps that table to the chart.
- **Local models:** the dashboard finds Ollama, LM Studio, vLLM, llama.cpp, MLX, and Jan. It also recommends models that fit your computer.
- **Your own keys:** it takes keys for Gemini, Anthropic, OpenAI, OpenRouter, and NVIDIA, or any OpenAI-compatible URL. Keys stay in the local server.
- **ParseBench:** runs use the ParseBench prompts word for word, and the official evaluator gives the scores.

Your document stays on your computer until you choose a cloud model. Then only the pages that you parse go to that provider.

Install the skill:

```bash
npx skills add okrapdf/skills --skill okrapdf
```

Agents read [SKILL.md](SKILL.md). Humans can run `npx okrapdf --help`.
