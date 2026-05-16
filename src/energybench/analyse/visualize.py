"""
Visualization tools for bias detection results.
"""

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

from energybench.analyze.bias_detection import BiasDetectionResult


# Swiss-inspired color palette (Tufte style)
SWISS_RED = "#B55A52"
SOFT_GREY = "#808080"
MID_GREY = "0.65"
LIGHT_GREY = "#C7C7C7"
DARK_GREY = "0.35"


def set_tufte_style():
    """Apply Tufte-inspired minimalist style with Swiss colors."""
    plt.rcParams.update({
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": True,
        "axes.spines.bottom": True,
        "axes.grid": True,
        "grid.color": "0.85",
        "grid.linestyle": "-",
        "grid.linewidth": 0.5,
        "axes.edgecolor": DARK_GREY,
        "axes.linewidth": 0.8,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "xtick.color": "0.25",
        "ytick.color": "0.25",
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "axes.labelsize": 9,
        "axes.labelcolor": "0.2",
        "axes.titlesize": 11,
        "axes.titleweight": "normal",
        "legend.fontsize": 8,
        "legend.frameon": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })


def apply_spine_style(ax):
    """Apply spine styling to an axes object."""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(0.6)
    ax.spines['bottom'].set_linewidth(0.6)
    ax.spines['left'].set_color(DARK_GREY)
    ax.spines['bottom'].set_color(DARK_GREY)


def plot_bias_detection_overview(
    result: BiasDetectionResult,
    output_path: Optional[Path] = None,
    figsize: tuple[float, float] = (16, 14),
    dpi: int = 100,
) -> None:
    """
    Create comprehensive visualization of bias detection results.
    
    6-panel layout:
    Row 1: Bias %, MAE/RMSE, Correlation
    Row 2: Daily Comparison, Correlation Stability, Confidence Timeline
    Row 3: Recommended Methods (full width)
    
    Parameters
    ----------
    result : BiasDetectionResult
        Detection results to visualize
    output_path : Path, optional
        Path to save figure
    figsize : tuple
        Figure size in inches
    dpi : int
        Resolution for saved figure
    """
    set_tufte_style()
    
    # Extract data from windows
    if not result.rolling_windows:
        print("No rolling windows to plot")
        return
    
    timestamps = [w.start for w in result.rolling_windows]
    bias_pct = [w.bias_pct for w in result.rolling_windows]
    mae = [w.mae for w in result.rolling_windows]
    rmse = [w.rmse for w in result.rolling_windows]
    pearson = [w.pearson for w in result.rolling_windows]
    mean_indicator = [w.mean_indicator for w in result.rolling_windows]
    mean_target = [w.mean_target for w in result.rolling_windows]
    
    # Method colors (Swiss palette)
    method_colors = {
        'scaling': LIGHT_GREY,
        'advanced_scaling': MID_GREY,
        'benchmarking': SWISS_RED,
        'kalman': SOFT_GREY,
    }
    
    # Create figure with 3 rows
    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(3, 3, height_ratios=[1, 1, 0.6], hspace=0.35, wspace=0.3,
                          left=0.08, right=0.96, top=0.94, bottom=0.06)
    
    # Row 1: Bias, Errors, Correlation
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])
    
    # Row 2: Daily Comparison, Correlation Stability, Confidence
    ax4 = fig.add_subplot(gs[1, 0])
    ax5 = fig.add_subplot(gs[1, 1])
    ax6 = fig.add_subplot(gs[1, 2])
    
    # Row 3: Methods Timeline (full width)
    ax7 = fig.add_subplot(gs[2, :])
    
    # Apply spine styling to all axes
    for ax in [ax1, ax2, ax3, ax4, ax5, ax6, ax7]:
        apply_spine_style(ax)
    
    # ===== Panel 1: Bias percentage over time =====
    ax1.plot(timestamps, bias_pct, 'o-', color=SWISS_RED, linewidth=1.5, 
             markersize=3, alpha=0.8, label='Bias %')
    ax1.axhline(y=0, color=MID_GREY, linestyle='-', alpha=0.8, linewidth=1)
    ax1.axhline(y=5, color=SOFT_GREY, linestyle=':', alpha=0.6, linewidth=0.8)
    ax1.axhline(y=-5, color=SOFT_GREY, linestyle=':', alpha=0.6, linewidth=0.8)
    ax1.fill_between(timestamps, -5, 5, alpha=0.08, color=LIGHT_GREY)
    
    # Mark changepoints
    for cp in result.changepoints:
        if cp.metric_changed == "bias_pct":
            ax1.axvline(x=cp.timestamp, color=SWISS_RED, linestyle='--', 
                       alpha=0.4, linewidth=1)
    
    ax1.set_ylabel('Bias (%)', fontweight='normal')
    ax1.set_title('Bias over time', fontweight='normal', pad=8)
    ax1.grid(True, alpha=0.3, linewidth=0.5)
    
    # ===== Panel 2: MAE and RMSE over time =====
    ax2.plot(timestamps, mae, 'o-', linewidth=1.5, markersize=3, 
             label='MAE', color=SOFT_GREY, alpha=0.8)
    ax2.plot(timestamps, rmse, 's-', linewidth=1.5, markersize=3, 
             label='RMSE', color=MID_GREY, alpha=0.8)
    
    # Mark changepoints
    for cp in result.changepoints:
        if cp.metric_changed in ["mae", "rmse"]:
            ax2.axvline(x=cp.timestamp, color=SWISS_RED, linestyle='--', 
                       alpha=0.4, linewidth=1)
    
    ax2.set_ylabel('Error (GWh)', fontweight='normal')
    ax2.set_title('Error metrics', fontweight='normal', pad=8)
    ax2.legend(loc='upper right', fontsize=8, frameon=False)
    ax2.grid(True, alpha=0.3, linewidth=0.5)
    
    # ===== Panel 3: Correlation over time =====
    ax3.plot(timestamps, pearson, 'o-', linewidth=1.5, markersize=3, 
             label='Pearson r', color=SOFT_GREY, alpha=0.8)
    ax3.axhline(y=0.9, color=SWISS_RED, linestyle=':', alpha=0.5, linewidth=0.8)
    ax3.axhline(y=0.7, color=SOFT_GREY, linestyle=':', alpha=0.5, linewidth=0.8)
    ax3.fill_between(timestamps, 0.9, 1.0, alpha=0.08, color=LIGHT_GREY)
    
    # Mark changepoints
    for cp in result.changepoints:
        if cp.metric_changed == "pearson":
            ax3.axvline(x=cp.timestamp, color=SWISS_RED, linestyle='--', 
                       alpha=0.4, linewidth=1)
    
    ax3.set_ylabel('Correlation', fontweight='normal')
    ax3.set_title('Shape similarity', fontweight='normal', pad=8)
    ax3.set_ylim(0, 1.05)
    ax3.grid(True, alpha=0.3, linewidth=0.5)
    
    # ===== Panel 4: Daily Aggregation Comparison =====
    ax4.plot(timestamps, mean_indicator, linewidth=1.2, 
             color=LIGHT_GREY, alpha=0.9, label='Indicator')
    ax4.plot(timestamps, mean_target, linewidth=1.2, 
             color=SWISS_RED, alpha=0.9, label='Target')
    
    ax4.set_ylabel('Daily mean (GWh)', fontweight='normal')
    ax4.set_title('Daily aggregation', fontweight='normal', pad=8)
    ax4.legend(loc='upper right', fontsize=8, frameon=False)
    ax4.grid(True, alpha=0.3, linewidth=0.5)
    
    # ===== Panel 5: Correlation Stability =====
    # Calculate rolling correlation stability (variance in correlation)
    if len(pearson) > 5:
        window = 5
        corr_stability = []
        corr_timestamps = []
        for i in range(len(pearson) - window + 1):
            corr_window = pearson[i:i+window]
            corr_stability.append(np.std(corr_window))
            corr_timestamps.append(timestamps[i + window//2])
        
        ax5.plot(corr_timestamps, corr_stability, 'o-', linewidth=1.5, 
                markersize=3, color=SOFT_GREY, alpha=0.8)
        ax5.axhline(y=0.05, color=SWISS_RED, linestyle=':', alpha=0.5, linewidth=0.8,
                   label='Stability threshold')
        ax5.fill_between(corr_timestamps, 0, 0.05, alpha=0.08, color=LIGHT_GREY)
    
    ax5.set_ylabel('Correlation std dev', fontweight='normal')
    ax5.set_title('Correlation stability', fontweight='normal', pad=8)
    ax5.legend(loc='upper right', fontsize=8, frameon=False)
    ax5.grid(True, alpha=0.3, linewidth=0.5)
    
    # ===== Panel 6: Confidence Timeline =====
    if result.recommendations:
        # Extract confidence scores over time
        rec_starts = [rec.start for rec in result.recommendations]
        rec_confidence = [rec.confidence for rec in result.recommendations]
        rec_methods = [rec.recommended_method for rec in result.recommendations]
        
        # Plot confidence as line with method-colored markers
        for i, (start, conf, method) in enumerate(zip(rec_starts, rec_confidence, rec_methods)):
            color = method_colors.get(method, SOFT_GREY)
            ax6.plot(start, conf, 'o', markersize=5, color=color, alpha=0.8)
        
        # Connect with line
        ax6.plot(rec_starts, rec_confidence, '-', linewidth=1, 
                color=MID_GREY, alpha=0.5)
        
        ax6.axhline(y=0.8, color=SWISS_RED, linestyle=':', alpha=0.5, linewidth=0.8,
                   label='High confidence')
        ax6.fill_between([min(rec_starts), max(rec_starts)], 0.8, 1.0, 
                        alpha=0.08, color=LIGHT_GREY)
    
    ax6.set_ylabel('Confidence', fontweight='normal')
    ax6.set_title('Recommendation confidence', fontweight='normal', pad=8)
    ax6.set_ylim(0, 1.05)
    ax6.legend(loc='lower right', fontsize=8, frameon=False)
    ax6.grid(True, alpha=0.3, linewidth=0.5)
    
    # ===== Panel 7: Recommended Methods Timeline =====
    if result.recommendations:
        sorted_recs = sorted(result.recommendations, key=lambda x: x.start)
        
        for i, rec in enumerate(sorted_recs):
            duration = (rec.end - rec.start).days
            color = method_colors.get(rec.recommended_method, SOFT_GREY)
            
            # Bar height based on confidence
            height = rec.confidence * 0.8
            
            ax7.barh(
                0,
                duration,
                left=rec.start,
                height=height,
                color=color,
                alpha=0.7,
                edgecolor=DARK_GREY,
                linewidth=0.5,
            )
            
            # Add method label if space allows
            mid_point = rec.start + (rec.end - rec.start) / 2
            if duration > 20:  # Only show text for periods > 20 days
                method_short = rec.recommended_method.replace('_', '\n')
                ax7.text(
                    mid_point,
                    0,
                    method_short,
                    ha='center',
                    va='center',
                    fontsize=7,
                    fontweight='normal',
                    color='white' if rec.recommended_method == 'benchmarking' else '0.2',
                )
        
        # Create legend
        legend_patches = [
            mpatches.Patch(color=color, label=method.replace('_', ' ').title(), alpha=0.7)
            for method, color in method_colors.items()
        ]
        ax7.legend(handles=legend_patches, loc='upper right', fontsize=8, 
                  ncol=4, frameon=False)
        
        ax7.set_ylabel('Confidence\n(bar height)', fontweight='normal', fontsize=8)
        ax7.set_yticks([])
        ax7.set_ylim(-0.5, 0.5)
    else:
        ax7.text(
            0.5, 0.5, 'No recommendations generated',
            ha='center', va='center', transform=ax7.transAxes,
            fontsize=10, color=SOFT_GREY,
        )
        ax7.set_yticks([])
    
    ax7.set_xlabel('Date', fontweight='normal')
    ax7.set_title('Recommended adjustment methods', fontweight='normal', pad=8)
    ax7.grid(True, alpha=0.3, axis='x', linewidth=0.5)
    
    # Format x-axis for all time-based plots
    for ax in [ax1, ax2, ax3, ax4, ax5, ax6, ax7]:
        ax.tick_params(axis='x', rotation=0)
        fig.autofmt_xdate(rotation=45, ha='right')
    
    # Overall title
    fig.suptitle(
        f'Bias Detection Analysis: {result.variable}\n'
        f'Overall Bias: {result.overall_bias_pct:+.2f}% | '
        f'MAE: {result.overall_mae:.2f} | '
        f'RMSE: {result.overall_rmse:.2f} | '
        f'Changepoints: {len(result.changepoints)} | '
        f'Clusters: {len(result.clusters)}',
        fontsize=13,
        fontweight='normal',
        y=0.98,
    )
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white')
        print(f"📊 Visualization saved to: {output_path}")
    else:
        plt.show()
    
    plt.close()


def plot_cluster_characteristics(
    result: BiasDetectionResult,
    output_path: Optional[Path] = None,
    figsize: tuple[float, float] = (12, 8),
    dpi: int = 100,
) -> None:
    """
    Visualize characteristics of detected clusters with Swiss styling.
    
    Parameters
    ----------
    result : BiasDetectionResult
        Detection results with clusters
    output_path : Path, optional
        Path to save figure
    figsize : tuple
        Figure size in inches
    dpi : int
        Resolution for saved figure
    """
    set_tufte_style()
    
    if not result.clusters:
        print("No clusters to visualize")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    
    # Apply spine styling to all axes
    for ax_row in axes:
        for ax in ax_row:
            apply_spine_style(ax)
    
    cluster_ids = [c.cluster_id for c in result.clusters]
    n_periods = [c.n_periods for c in result.clusters]
    mean_bias = [c.mean_bias_pct for c in result.clusters]
    mean_mae = [c.mean_mae for c in result.clusters]
    mean_rmse = [c.mean_rmse for c in result.clusters]
    mean_pearson = [c.mean_pearson for c in result.clusters]
    
    # 1. Number of periods per cluster
    ax1 = axes[0, 0]
    bars1 = ax1.bar(cluster_ids, n_periods, color=SOFT_GREY, alpha=0.7, 
                    edgecolor=DARK_GREY, linewidth=0.6)
    ax1.set_xlabel('Cluster ID', fontweight='normal')
    ax1.set_ylabel('Number of Periods', fontweight='normal')
    ax1.set_title('Cluster sizes', fontweight='normal')
    ax1.grid(True, alpha=0.3, axis='y', linewidth=0.5)
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2., height,
            f'{int(height)}',
            ha='center', va='bottom', fontsize=9, fontweight='normal',
        )
    
    # 2. Mean bias per cluster
    ax2 = axes[0, 1]
    colors = [SWISS_RED if b < 0 else SOFT_GREY for b in mean_bias]
    bars2 = ax2.bar(cluster_ids, mean_bias, color=colors, alpha=0.7, 
                    edgecolor=DARK_GREY, linewidth=0.6)
    ax2.axhline(y=0, color=MID_GREY, linestyle='-', alpha=0.8, linewidth=1)
    ax2.set_xlabel('Cluster ID', fontweight='normal')
    ax2.set_ylabel('Mean Bias (%)', fontweight='normal')
    ax2.set_title('Bias by cluster', fontweight='normal')
    ax2.grid(True, alpha=0.3, axis='y', linewidth=0.5)
    
    # 3. MAE and RMSE per cluster
    ax3 = axes[1, 0]
    x = np.arange(len(cluster_ids))
    width = 0.35
    ax3.bar(x - width/2, mean_mae, width, label='MAE', color=SOFT_GREY, 
            alpha=0.7, edgecolor=DARK_GREY, linewidth=0.6)
    ax3.bar(x + width/2, mean_rmse, width, label='RMSE', color=MID_GREY, 
            alpha=0.7, edgecolor=DARK_GREY, linewidth=0.6)
    ax3.set_xlabel('Cluster ID', fontweight='normal')
    ax3.set_ylabel('Error (GWh)', fontweight='normal')
    ax3.set_title('Error metrics by cluster', fontweight='normal')
    ax3.set_xticks(x)
    ax3.set_xticklabels(cluster_ids)
    ax3.legend(frameon=False, fontsize=8)
    ax3.grid(True, alpha=0.3, axis='y', linewidth=0.5)
    
    # 4. Correlation per cluster
    ax4 = axes[1, 1]
    bars4 = ax4.bar(cluster_ids, mean_pearson, color=SOFT_GREY, alpha=0.7, 
                    edgecolor=DARK_GREY, linewidth=0.6)
    ax4.axhline(y=0.9, color=SWISS_RED, linestyle=':', alpha=0.5, linewidth=0.8)
    ax4.axhline(y=0.7, color=SOFT_GREY, linestyle=':', alpha=0.5, linewidth=0.8)
    ax4.set_xlabel('Cluster ID', fontweight='normal')
    ax4.set_ylabel('Mean Pearson r', fontweight='normal')
    ax4.set_title('Correlation by cluster', fontweight='normal')
    ax4.set_ylim(0, 1.05)
    ax4.grid(True, alpha=0.3, axis='y', linewidth=0.5)
    
    # Add explanatory subtitle
    fig.text(
        0.5, 0.96,
        f'Each cluster groups rolling windows with similar bias patterns | '
        f'Total windows analyzed: {sum(n_periods)}',
        ha='center',
        va='top',
        fontsize=9,
        color=SOFT_GREY,
        style='italic',
    )
    
    plt.suptitle(
        f'Cluster Characteristics: {result.variable}',
        fontsize=13,
        fontweight='normal',
        y=0.99,
    )
    
    plt.tight_layout()
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white')
        print(f"📊 Cluster visualization saved to: {output_path}")
    else:
        plt.show()
    
    plt.close()


def plot_recommendation_timeline(
    result: BiasDetectionResult,
    output_path: Optional[Path] = None,
    figsize: tuple[float, float] = (14, 6),
    dpi: int = 100,
) -> None:
    """
    Create a timeline view of recommendations with confidence levels (Swiss style).
    
    Parameters
    ----------
    result : BiasDetectionResult
        Detection results with recommendations
    output_path : Path, optional
        Path to save figure
    figsize : tuple
        Figure size in inches
    dpi : int
        Resolution for saved figure
    """
    set_tufte_style()
    
    if not result.recommendations:
        print("No recommendations to visualize")
        return
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Apply spine styling
    apply_spine_style(ax)
    
    # Method colors (Swiss palette)
    method_colors = {
        'scaling': LIGHT_GREY,
        'advanced_scaling': MID_GREY,
        'benchmarking': SWISS_RED,
        'kalman': SOFT_GREY,
    }
    
    # Sort recommendations by start date
    sorted_recs = sorted(result.recommendations, key=lambda x: x.start)
    
    # Plot each recommendation
    for i, rec in enumerate(sorted_recs):
        duration = (rec.end - rec.start).days
        color = method_colors.get(rec.recommended_method, SOFT_GREY)
        
        # Bar height based on confidence
        height = rec.confidence
        
        ax.barh(
            i,
            duration,
            left=rec.start,
            height=height,
            color=color,
            alpha=0.8,
            edgecolor=DARK_GREY,
            linewidth=0.6,
        )
        
        # Add method label
        mid_point = rec.start + (rec.end - rec.start) / 2
        method_display = rec.recommended_method.replace('_', '\n')
        text_color = 'white' if rec.recommended_method == 'benchmarking' else '0.2'
        ax.text(
            mid_point,
            i,
            method_display,
            ha='center',
            va='center',
            fontsize=7,
            fontweight='normal',
            color=text_color,
        )
        
        # Add confidence on the right
        ax.text(
            rec.end,
            i,
            f' {rec.confidence:.0%}',
            ha='left',
            va='center',
            fontsize=8,
            fontweight='normal',
            color=DARK_GREY,
        )
    
    # Create legend
    legend_patches = [
        mpatches.Patch(color=color, label=method.replace('_', ' ').title(), alpha=0.8)
        for method, color in method_colors.items()
    ]
    ax.legend(handles=legend_patches, loc='upper right', fontsize=9, 
             ncol=2, frameon=False)
    
    ax.set_xlabel('Date', fontsize=10, fontweight='normal')
    ax.set_ylabel('Recommendation #', fontsize=10, fontweight='normal')
    ax.set_title(
        f'Adjustment Method Recommendations: {result.variable}\n'
        f'Bar height = confidence level',
        fontsize=12,
        fontweight='normal',
        pad=12,
    )
    ax.set_yticks(range(len(sorted_recs)))
    ax.set_yticklabels([f'#{i+1}' for i in range(len(sorted_recs))])
    ax.grid(True, alpha=0.3, axis='x', linewidth=0.5)
    
    fig.autofmt_xdate(rotation=45, ha='right')
    plt.tight_layout()
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white')
        print(f"📊 Timeline visualization saved to: {output_path}")
    else:
        plt.show()
    
    plt.close()