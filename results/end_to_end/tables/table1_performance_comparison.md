# Table 1: Performance Comparison

Sequential vs Hybrid Execution Mode Performance (600s Timeout)

## Markdown Format

| Group Name | Tasks | Structure | Sequential Time (s) | Hybrid Time (s) | Speedup | Best Mode |
|------------|-------|-----------|---------------------|-----------------|---------|-----------|
| db_product_sales | 2 | Linear | 63.60 | 91.14 | 0.70× | Sequential |
| os_user_analysis | 3 | Linear | 100.04 | 63.70 | **1.57×** | **Hybrid** |
| os_system_health_fanout | 8 | Fan-out | 244.51 | 245.19 | 1.00× | Sequential |
| web_scraping_fanout | 12 | Fan-out | 401.00 | 305.54 | **1.31×** | **Hybrid** |
| data_pipeline_mixed | 16 | Mixed | 791.61 | 598.55 | **1.32×** | **Hybrid** |
| **TOTAL** | **41** | - | **1600.76** | **1304.12** | **1.23×** | **Hybrid** |

## LaTeX Format

```latex
\begin{table}[h]
\centering
\caption{Sequential vs Hybrid Execution Mode Performance Comparison}
\label{tab:performance}
\begin{tabular}{lccrrrl}
\toprule
\textbf{Group} & \textbf{Tasks} & \textbf{Structure} & \textbf{Seq (s)} & \textbf{Hybrid (s)} & \textbf{Speedup} & \textbf{Best} \\
\midrule
db\_product\_sales & 2 & Linear & 63.60 & 91.14 & 0.70$\times$ & Sequential \\
os\_user\_analysis & 3 & Linear & 100.04 & 63.70 & \textbf{1.57$\times$} & \textbf{Hybrid} \\
os\_system\_health\_fanout & 8 & Fan-out & 244.51 & 245.19 & 1.00$\times$ & Sequential \\
web\_scraping\_fanout & 12 & Fan-out & 401.00 & 305.54 & \textbf{1.31$\times$} & \textbf{Hybrid} \\
data\_pipeline\_mixed & 16 & Mixed & 791.61 & 598.55 & \textbf{1.32$\times$} & \textbf{Hybrid} \\
\midrule
\textbf{TOTAL} & \textbf{41} & -- & \textbf{1600.76} & \textbf{1304.12} & \textbf{1.23$\times$} & \textbf{Hybrid} \\
\bottomrule
\end{tabular}
\end{table}
```

## Key Findings

- **Total Time Saved**: 296.64 seconds (18.5% improvement)
- **Average Speedup**: 1.23×
- **Success Rate**: 100% across all 41 tasks
- **Best Performers**: web_scraping_fanout (1.31×), data_pipeline_mixed (1.32×), os_user_analysis (1.57×)
- **Regression Cases**: db_product_sales (0.70×), os_system_health_fanout (0.997×)

## Usage in Paper

**Introduction**: Cite this table when presenting overall evaluation results.

**Evaluation Section**: Reference as "Table 1 presents the performance comparison..."

**Discussion**: Use to support claims about task scale threshold (≥12 tasks).
