import re
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

ablation_lines = Path('ablation.md').read_text().splitlines()
current_group = None
stats = {
    1: {'total': 0, 'corr': 0, 'feas': 0, 'read': 0, 'count': 0},
    2: {'total': 0, 'corr': 0, 'feas': 0, 'read': 0, 'count': 0},
    3: {'total': 0, 'corr': 0, 'feas': 0, 'read': 0, 'count': 0},
}
ref_counts = {'highly relate': 0, 'low relate': 0, 'no relation': 0}

score_pattern = re.compile(r'---\s+([^:]+):<(\d+)/10\s+\((\d+)\+(\d+)\+(\d+)\)>')
ref_pattern = re.compile(r'\[ref:(highly relate|low relate|no relation)\]')

for line in ablation_lines:
    stripped = line.strip()
    if stripped.startswith('- <Group'):
        match = re.search(r'<Group\s+(\d+)>', stripped)
        if match:
            current_group = int(match.group(1))
        continue
    if not line.startswith('--- '):
        continue
    entry = score_pattern.match(line)
    if not entry:
        raise ValueError(f"Cannot parse score line: {line}")
    total = int(entry.group(2))
    corr = int(entry.group(3))
    feas = int(entry.group(4))
    read = int(entry.group(5))
    stats[current_group]['total'] += total
    stats[current_group]['corr'] += corr
    stats[current_group]['feas'] += feas
    stats[current_group]['read'] += read
    stats[current_group]['count'] += 1
    if current_group == 3:
        ref_match = ref_pattern.search(line)
        if not ref_match:
            raise ValueError(f"Missing ref tag on Group 3 line: {line}")
        ref_counts[ref_match.group(1)] += 1

labels = ['Group 1', 'Group 2', 'Group 3']
counts = np.array([stats[g]['count'] for g in (1, 2, 3)], dtype=float)
avg_totals = np.array([stats[g]['total'] for g in (1, 2, 3)], dtype=float) / counts

plt.figure(figsize=(6, 5))
plt.bar(labels, avg_totals, color='#1f77b4')
plt.xlabel('Evaluation Group')
plt.ylabel('Average Total Score (0-10)')
plt.title('Average Rule Quality per Group')
plt.ylim(0, 10)
for idx, value in enumerate(avg_totals):
    plt.text(idx, value + 0.1, f"{value:.1f}", ha='center')
plt.tight_layout()

component_avgs = [
    ('Correctness & Factuality (max 4)', np.array([stats[g]['corr'] for g in (1, 2, 3)], dtype=float) / counts),
    ('Engineering Feasibility (max 3)', np.array([stats[g]['feas'] for g in (1, 2, 3)], dtype=float) / counts),
    ('Contextless Readability (max 3)', np.array([stats[g]['read'] for g in (1, 2, 3)], dtype=float) / counts),
]
plt.figure(figsize=(7, 5))
x = np.arange(len(labels))
width = 0.25
for i, (label, values) in enumerate(component_avgs):
    offsets = x + (i - 1) * width
    bars = plt.bar(offsets, values, width, label=label)
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height + 0.05, f"{height:.1f}", ha='center', va='bottom', fontsize=8)
plt.xticks(x, labels)
plt.xlabel('Evaluation Group')
plt.ylabel('Average Component Score')
plt.title('Average Component Scores per Group')
plt.ylim(0, 5)
plt.legend()
plt.tight_layout()

relation_labels = ['highly relate', 'low relate', 'no relation']
relation_colors = ['#1f77b4', '#ff7f0e', '#7f7f7f']
relation_sizes = [ref_counts[label] for label in relation_labels]
plt.figure(figsize=(5.5, 5.5))
plt.pie(
    relation_sizes,
    labels=[f"{label} ({count})" for label, count in zip(relation_labels, relation_sizes)],
    colors=relation_colors,
    autopct='%1.0f%%',
    startangle=90,
    textprops={'color': 'black'}
)
plt.title('Group 3 Rule Ref Relevance')
plt.tight_layout()

plt.show()
