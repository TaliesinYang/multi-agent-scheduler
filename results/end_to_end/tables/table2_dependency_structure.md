# Table 2: Dependency Structure Impact Analysis

Performance Analysis by Dependency Structure Type (600s Timeout)

## Markdown Format

| Structure Type | Groups | Avg Tasks | Avg Seq Time (s) | Avg Hybrid Time (s) | Avg Speedup | Success Rate | Observations |
|----------------|--------|-----------|------------------|---------------------|-------------|--------------|--------------|
| Linear | 2 | 2.5 | 81.82 | 77.42 | **1.13×** | 100% | Highly variable (0.70× - 1.57×); depends on task granularity |
| Fan-out | 2 | 10.0 | 322.75 | 275.37 | **1.15×** | 100% | Requires ≥12 tasks for advantage; overhead significant for small fan-outs |
| Mixed | 1 | 16.0 | 791.61 | 598.55 | **1.32×** | 100% | Most stable performance; complexity amortizes overhead |

## LaTeX Format

```latex
\begin{table}[h]
\centering
\caption{Performance Analysis by Dependency Structure Type}
\label{tab:structure_impact}
\begin{tabular}{lccrrrlp{4cm}}
\toprule
\textbf{Structure} & \textbf{Groups} & \textbf{Avg Tasks} & \textbf{Avg Seq (s)} & \textbf{Avg Hybrid (s)} & \textbf{Avg Speedup} & \textbf{Success} & \textbf{Observations} \\
\midrule
Linear & 2 & 2.5 & 81.82 & 77.42 & \textbf{1.13$\times$} & 100\% & Highly variable (0.70× - 1.57×); depends on task granularity \\
Fan-out & 2 & 10.0 & 322.75 & 275.37 & \textbf{1.15$\times$} & 100\% & Requires ≥12 tasks for advantage; overhead significant for small fan-outs \\
Mixed & 1 & 16.0 & 791.61 & 598.55 & \textbf{1.32$\times$} & 100\% & Most stable performance; complexity amortizes overhead \\
\bottomrule
\end{tabular}
\end{table}
```

## Key Findings

- **Linear Dependencies**: Most unpredictable (0.70× - 1.57× range)
- **Fan-out Dependencies**: Scale-dependent; small fan-outs (8 tasks) show no benefit
- **Mixed DAG**: Most consistent and reliable for complex workflows

## Usage in Paper

**Methodology**: Reference when explaining test group selection rationale.

**Results**: Use to analyze performance trends by structure type.

**Discussion**: Support claims about optimal dependency patterns for parallelization.
