fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, height_ratios=[3, 1])

adj_daily.plot(ax=ax1, label='Benchmarked daily sum', color='tab:blue', linewidth=2.5)
low_hydro.plot(
    ax=ax1,
    label='SFOE daily target',
    color='tab:orange',
    linestyle='None',
    marker='o',
    markersize=7,
    markerfacecolor='white',
    markeredgewidth=2
)
ax1.set_title('Hydro daily totals: benchmarked vs SFOE')
ax1.set_ylabel('GWh')
ax1.grid(True, alpha=0.3)
ax1.legend()

difference = adj_daily - low_hydro
difference.plot(ax=ax2, color='tab:red', marker='o', linewidth=1.5)
ax2.axhline(0, color='black', linestyle='--', linewidth=1)
ax2.set_title('Daily difference')
ax2.set_ylabel('GWh')
ax2.set_xlabel('Date')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('output/hydro_validation_with_difference.png', dpi=150, bbox_inches='tight')
plt.show()
