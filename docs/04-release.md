# 发布流程

> 本文描述本 fork 的发布门禁与产物。所有数字都由 `tools/sync_doc_numbers.py`
> 从当前树重新测量，文档里出现的数不允许手写。

## 1. 版本与标签

- 版本号形如 `v0.12.0-fork.N`，对应上游 `configure.ac` 里的 `0.12.0+dev` 基线，
  `N` 从 1 递增。
- 标签一旦推送就不再移动：每个 `v*` 标签在 GitHub Release 上必须始终可取。
- 打包流水线只在推送 `v*` 标签时才创建 Release
  （`.github/workflows/snapshot.yml` 的 `release` job，`if: startsWith(github.ref, 'refs/tags/v')`）。

## 2. 发布前：重生成生成物

`docs/01-inventory.md` 与 `docs/03-LICENSES.md` 是生成物（文件头写明「请勿手改」），
发布前必须重跑；`README.md`、`README.zh-CN.md`、`docs/00-findings.md`、`docs/02-usage.md`
里的数字由 `tools/sync_doc_numbers.py` 就地同步。

> `tools/sync_doc_numbers.py` 统计的「本树文件数」取自 `git ls-files`（索引），
> 所以**新增文件要先 `git add` 再跑**，否则它会数不到新文件、发布出去的数字少几份。

```bash
python3 tools/gen_report.py       # -> docs/01-inventory.md + manifest/consolidated.csv
python3 tools/gen_licenses.py     # -> docs/03-LICENSES.md + manifest/licenses.csv
python3 tools/sync_doc_numbers.py # 就地落数字（不带 --check 时才会写文件）
```

## 3. 发布门禁（CI 的 gate job 跑的就是这里的前两条）

```bash
python3 tools/verify_tree.py                 # 清单与树必须逐条对上
python3 tools/sync_doc_numbers.py --check     # 任何已发布数字漂移都非 0 退出
```

`verify_tree.py` 必须打印 `VERIFY: PASS`；`--check` 必须打印
`sync_doc_numbers: OK (0 pending)` 并以 0 退出。任何一条不满足就不打标签。

## 4. 发布后必须复跑的 4 条命令

标签推上去、打包完成后，在干净检出（`git clone` + `git checkout vX`）里复跑下面
4 条。它们分别覆盖：清单完整性、已发布数字、配置文件互相引用的可达性、TCL 可解析性。

```bash
# 1) 清单完整性：每个第三方文件都有来源记录，且摘要一致
python3 tools/verify_tree.py

# 2) 已发布数字：README / docs 里的每个数字都能从当前树复算出来
python3 tools/sync_doc_numbers.py --check

# 3) 引用可达性：所有 source [find ...] 都能在树里找到目标（已知 5 条无害，见下）
python3 tools/audit_dangling_refs.py

# 4) TCL 可解析性：每个 .cfg/.tcl 的括号与引号在解释器眼里都是完整的
#    需要 tclsh（Debian/Ubuntu：apt-get install tcl）；没有解释器时该脚本打印 SKIP 并退 0
python3 tools/check_tcl_syntax.py
```

当前树上的期望输出：

| 命令 | 期望 |
|---|---|
| `verify_tree.py` | `recorded : 767` / `on disk : 767` / `errors : 0` / `warns : 25` / `VERIFY: PASS` |
| `sync_doc_numbers.py --check` | `sync_doc_numbers: OK (0 pending)`，退出码 0 |
| `audit_dangling_refs.py` | 扫描 1771 个 `.cfg` + 47 个 `.tcl`，解析 1942 条引用，`unresolved references: 5`（全部无害：3 条注释行、1 个上游占位符、1 条注释路径多写了一级目录） |
| `check_tcl_syntax.py` | `check_tcl_syntax: OK (1818 files parsed, 0 problems)` |

上游继承来的文件（`upstream/master` 里同名同内容）不在这些检查的范围内：
`verify_tree.py` 只核对导入清单里的文件，`sync_doc_numbers.py` 只复算文档里
已发布的数字。

## 5. 已知不阻塞发布的事项

- 25 条 `verify_tree.py` 警告中，24 条是来源仓库在 GitHub 上解析不出许可证，
  1 条是同名不同内容的文件被本 fork 有意保留（`tcl/target/adspsc58x.cfg`）。
- 18 个已导入的 C 文件未接线进构建；卡点见 `docs/02-usage.md` 的「C 驱动的接入状态」。
- 401 个导入的配置仍用已废弃的 `-chain-position` 写法（493 处）。上游选项
  仍然可用，因此不影响发布，但它是一处待清理项。

## 6. 本地没有发布环境时的替代验证

本地没有 `gcc`/`make`/`autoconf` 时，编译只能由 CI 的 `package` job 覆盖；本地可以做的是
静态接线检查：

```bash
python3 tools/sync_doc_numbers.py --check   # 含「47 接线 / 18 未接线」的复算
python3 tools/verify_tree.py                # 含每个 .cfg 的花括号平衡检查
```
