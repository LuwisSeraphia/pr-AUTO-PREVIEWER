<CLUSTER 1>
file:{xxx.json,xxx.json,.....}
- <Group 1> (baseline): Generate rules using only the template, no abstraction requirement, no rule_ref link.
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>

- <Group 2> (template + abstraction): Generate rules using the template and the abstraction requirements (avoid variable names, generalize rules), but do NOT use rule_ref links.
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>

- <Group 3> (template + abstraction + rule_ref): Generate rules using template, abstraction requirements, and incorporate rule_ref links (from templates/rule_ref.md or user-provided map) when applicable.
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>


------------------------------------------------------------------------
<CLUSTER 2>
file:{xxx.json,xxx.json,.....}
- <Group 1> (baseline): Generate rules using only the template, no abstraction requirement, no rule_ref link.
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>

- <Group 2> (template + abstraction): Generate rules using the template and the abstraction requirements (avoid variable names, generalize rules), but do NOT use rule_ref links.
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>

- <Group 3> (template + abstraction + rule_ref): Generate rules using template, abstraction requirements, and incorporate rule_ref links (from templates/rule_ref.md or user-provided map) when applicable.
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>
--- xxx.json:<rule description>


......



conclusion:......