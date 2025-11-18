# Table 5: Detailed Metrics Per Group

Complete Experimental Data (600s Timeout)

## Markdown Format

| Group | Tasks | Batches | Seq Time (s) | Seq Success | Seq Failed | Hybrid Time (s) | Hybrid Success | Hybrid Failed | Speedup | Time Saved (s) |
|-------|-------|---------|--------------|-------------|------------|-----------------|----------------|---------------|---------|----------------|
| db_product_sales | 2 | 0 | 63.60 | 100% | 0 | 91.14 | 100% | 0 | 0.70× | -27.54 |
| os_user_analysis | 3 | 0 | 100.04 | 100% | 0 | 63.70 | 100% | 0 | **1.57×** | **+36.35** |
| os_system_health_fanout | 8 | 0 | 244.51 | 100% | 0 | 245.19 | 100% | 0 | 1.00× | -0.68 |
| web_scraping_fanout | 12 | 0 | 401.00 | 100% | 0 | 305.54 | 100% | 0 | **1.31×** | **+95.45** |
| data_pipeline_mixed | 16 | 0 | 791.61 | 100% | 0 | 598.55 | 100% | 0 | **1.32×** | **+193.06** |
| **TOTAL** | **41** | **0** | **1600.76** | **100%** | **0** | **1304.12** | **100%** | **0** | **1.23×** | **+296.64** |

## LaTeX Format

```latex
\begin{table}[h]
\centering
\caption{Detailed Experimental Metrics Per Test Group}
\label{tab:detailed_metrics}
\begin{tabular}{lcccccccccc}
\toprule
\textbf{Group} & \textbf{Tasks} & \textbf{Batches} & \textbf{Seq (s)} & \textbf{Seq Succ} & \textbf{Seq Fail} & \textbf{Hyb (s)} & \textbf{Hyb Succ} & \textbf{Hyb Fail} & \textbf{Speedup} & \textbf{Saved (s)} \\
\midrule
db\_product\_sales & 2 & 0 & 63.60 & 100\% & 0 & 91.14 & 100\% & 0 & 0.70$\times$ & -27.54 \\
os\_user\_analysis & 3 & 0 & 100.04 & 100\% & 0 & 63.70 & 100\% & 0 & \textbf{1.57$\times$} & \textbf{+36.35} \\
os\_system\_health\_fanout & 8 & 0 & 244.51 & 100\% & 0 & 245.19 & 100\% & 0 & 1.00$\times$ & -0.68 \\
web\_scraping\_fanout & 12 & 0 & 401.00 & 100\% & 0 & 305.54 & 100\% & 0 & \textbf{1.31$\times$} & \textbf{+95.45} \\
data\_pipeline\_mixed & 16 & 0 & 791.61 & 100\% & 0 & 598.55 & 100\% & 0 & \textbf{1.32$\times$} & \textbf{+193.06} \\
\midrule
\textbf{TOTAL} & \textbf{41} & \textbf{0} & \textbf{1600.76} & \textbf{100\%} & \textbf{0} & \textbf{1304.12} & \textbf{100\%} & \textbf{0} & \textbf{1.23$\times$} & \textbf{+296.64} \\
\bottomrule
\end{tabular}
\end{table}
```

## Key Observations

- **Perfect Success Rate**: 100% across all modes (0 failures in 41 tasks)
- **Total Batches**: 0 parallel batches executed across 5 groups
- **Best Absolute Savings**: data_pipeline_mixed (+193.06s)
- **Largest Regression**: db_product_sales (-27.54s)
- **Net Benefit**: +296.64s (18.5% improvement)

## Usage in Paper

**Appendix**: Include as complete experimental data table.

**Results**: Reference specific values when discussing individual groups.

**Reproducibility**: Provides all metrics needed for result verification.
