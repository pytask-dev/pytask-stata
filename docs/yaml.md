# YAML Data Passed to Stata

pytask-stata serializes task keyword arguments with PyYAML and passes the path to the
generated YAML file as the first command line argument to the do-file. Inside Stata,
read the file with the user-written `yaml` package.

```stata
args config
yaml read using "`config'", locals replace
```

The `yaml` package stores parsed YAML in a Stata dataset with `key`, `value`, `level`,
`parent`, and `type` columns. With `locals`, scalar leaves are also available as
`r(yaml_<key>)` macros. Nested keys are flattened with underscores.

## Supported Types

| Python value                     | YAML shape                    | Stata representation                                                 | Access pattern                            |
| -------------------------------- | ----------------------------- | -------------------------------------------------------------------- | ----------------------------------------- |
| Non-empty `str`                  | `name: hello`                 | `type=string`, `value=hello`                                         | `r(yaml_name)`                            |
| `int`                            | `count: 42`                   | `type=numeric`, `value=42`                                           | `r(yaml_count)`                           |
| `float`                          | `ratio: 3.14`                 | `type=numeric`, `value=3.14`                                         | `r(yaml_ratio)`                           |
| `bool`                           | `enabled: true`               | `type=boolean`, `value=1` or `0`                                     | `r(yaml_enabled)`                         |
| `None`                           | `missing: null`               | `type=null`, empty value                                             | validate as `null`; no useful macro value |
| `pathlib.Path`                   | `path: build/out.dta`         | `type=string`, POSIX-style path                                      | `r(yaml_path)`                            |
| Flat `list` / `tuple` of scalars | `items:` plus `- value` lines | parent row plus `items_1`, `items_2`, ... rows with `type=list_item` | use flattened keys such as `items_1`      |
| Nested `dict` with scalar leaves | nested mapping                | flattened keys such as `config_child`                                | `yaml get config, attributes(child)`      |

## Recommended Limits

Keep the YAML bridge to configuration-like data: scalar values, paths, flat scalar
lists, and nested dictionaries with scalar leaves.

Avoid empty strings, lists of dictionaries, sets, bytes, decimals, and arbitrary Python
objects. PyYAML may emit YAML tags such as `!!set` or `!!binary`, or fail with a
`RepresenterError`; those forms are not useful as a stable Stata interface.
