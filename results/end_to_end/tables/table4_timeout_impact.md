# Table 4: Timeout Impact on Success Rate

Comparison of 60s vs 600s Timeout Configuration

## Markdown Format

| Group | 60s Seq Success | 60s Hybrid Success | 600s Seq Success | 600s Hybrid Success | Tasks Fixed | Impact |
|-------|-----------------|--------------------|-----------------|--------------------|-------------|--------|
| db_product_sales | 100.0% | 100.0% | 100.0% | 100.0% | 0 | No failures |
| os_user_analysis | 66.7% | 100.0% | 100.0% | 100.0% | 1 | **1 task(s) fixed** |
| os_system_health_fanout | 100.0% | 87.5% | 100.0% | 100.0% | 1 | **1 task(s) fixed** |
| web_scraping_fanout | 100.0% | 66.7% | 100.0% | 100.0% | 4 | **4 task(s) fixed** |
| data_pipeline_mixed | N/A | N/A | 100.0% | 100.0% | N/A | Only tested with 600s |

## LaTeX Format

```latex
\begin{table}[h]
\centering
\caption{Timeout Impact on Task Success Rate}
\label{tab:timeout_impact}
\begin{tabular}{lccccrl}
\toprule
\textbf{Group} & \textbf{60s Seq} & \textbf{60s Hybrid} & \textbf{600s Seq} & \textbf{600s Hybrid} & \textbf{Fixed} & \textbf{Impact} \\
\midrule
db\_product\_sales & 100.0\% & 100.0\% & 100.0\% & 100.0\% & 0 & No failures \\
os\_user\_analysis & 66.7\% & 100.0\% & 100.0\% & 100.0\% & 1 & 1 task(s) fixed \\
os\_system\_health\_fanout & 100.0\% & 87.5\% & 100.0\% & 100.0\% & 1 & 1 task(s) fixed \\
web\_scraping\_fanout & 100.0\% & 66.7\% & 100.0\% & 100.0\% & 4 & 4 task(s) fixed \\
data\_pipeline\_mixed & N/A & N/A & 100.0\% & 100.0\% & N/A & Only tested with 600s \\
\bottomrule
\end{tabular}
\end{table}
```

## Key Findings

- **Critical Discovery**: 60s timeout caused 6 task failures (14.6% failure rate)
- **600s Solution**: Achieved 100% success rate across all 41 tasks
- **Hybrid Mode Vulnerability**: Parallel execution paths more susceptible to timeout
- **Most Affected**: web_scraping_fanout (4 failures), os_system_health_fanout (1 failure)

## The "Speedup Paradox"

60s timeout results showed **artificially inflated speedup** metrics:
- db_product_sales: 1.55× (60s) → 0.70× (600s) - **False positive**
- os_system_health_fanout: 1.66× (60s) → 0.997× (600s) - **Masked overhead**

**Conclusion**: Only 600s timeout results represent true performance characteristics.

## Usage in Paper

**Methodology**: Justify timeout configuration choice.

**Evaluation**: Demonstrate measurement rigor and experimental validity.

**Discussion**: Explain why adequate timeout is critical for agent-based systems.
