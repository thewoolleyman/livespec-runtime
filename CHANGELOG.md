# Changelog

## [0.21.4](https://github.com/thewoolleyman/livespec-runtime/compare/v0.21.3...v0.21.4) (2026-08-25)


### Bug Fixes

* accept the internal prefix in the attention stable-ID grammar ([6421fcc](https://github.com/thewoolleyman/livespec-runtime/commit/6421fcc654c285c5fa11bac98d3a5a151febe04e))

## [0.21.3](https://github.com/thewoolleyman/livespec-runtime/compare/v0.21.2...v0.21.3) (2026-08-21)


### Bug Fixes

* distinguish unterminated governance defaults ([c795205](https://github.com/thewoolleyman/livespec-runtime/commit/c795205e08e0fbd279e1ac0726608e7c12691017))

## [0.21.2](https://github.com/thewoolleyman/livespec-runtime/compare/v0.21.1...v0.21.2) (2026-08-20)


### Bug Fixes

* **cross-repo:** put parse_depends_on_entry on the Result railway ([6bb42dc](https://github.com/thewoolleyman/livespec-runtime/commit/6bb42dc28bbdcbefa2d08aa2f3679c0dcc822dbf))
* **github-auth:** put load_github_app_config on the Result railway ([e60c681](https://github.com/thewoolleyman/livespec-runtime/commit/e60c6815ebece4e648c9c6efd9406b254e9cf2be))

## [0.21.1](https://github.com/thewoolleyman/livespec-runtime/compare/v0.21.0...v0.21.1) (2026-08-17)


### Bug Fixes

* **ci:** make export-ci-telemetry.sh ARG_MAX-safe ([ecbfa62](https://github.com/thewoolleyman/livespec-runtime/commit/ecbfa628224deff20983f460fea708a446ddf3ab))

## [0.21.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.20.2...v0.21.0) (2026-08-17)


### Features

* **ci:** batch the cheap checks — the matrices become batch jobs ([5210106](https://github.com/thewoolleyman/livespec-runtime/commit/52101068c0313c077658d87198db4a46a57b8c03))

## [0.20.2](https://github.com/thewoolleyman/livespec-runtime/compare/v0.20.1...v0.20.2) (2026-08-17)


### Bug Fixes

* **pre-commit:** wire repo-state checks into the doc-only subset ([ac8eab7](https://github.com/thewoolleyman/livespec-runtime/commit/ac8eab7d4986ed94da7083296d3f3b7eb7910b10))

## [0.20.1](https://github.com/thewoolleyman/livespec-runtime/compare/v0.20.0...v0.20.1) (2026-08-17)


### Bug Fixes

* **check:** harden the coverage dedup — clean-env producer + consume-once consumer ([c72c5aa](https://github.com/thewoolleyman/livespec-runtime/commit/c72c5aa41d25130c625be430a7f4c303431cd6ad))

## [0.20.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.19.0...v0.20.0) (2026-08-15)


### Features

* add awaits_scope_override field to WorkItem ([5bd4677](https://github.com/thewoolleyman/livespec-runtime/commit/5bd4677cc381d2b981c526e586f60fefade59201))

## [0.19.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.18.2...v0.19.0) (2026-08-13)


### Features

* expose spec PR merge governance key ([c230a31](https://github.com/thewoolleyman/livespec-runtime/commit/c230a31220f586fa0d4108fa0186868ba4e99ede))

## [0.18.2](https://github.com/thewoolleyman/livespec-runtime/compare/v0.18.1...v0.18.2) (2026-08-13)


### Bug Fixes

* **ci:** unshallow self-hosted checkout so origin/master..HEAD ranges resolve ([8fc4197](https://github.com/thewoolleyman/livespec-runtime/commit/8fc419773eef26b5cbdbc5764f4d7139548ee6e6))

## [0.18.1](https://github.com/thewoolleyman/livespec-runtime/compare/v0.18.0...v0.18.1) (2026-08-13)


### Bug Fixes

* **ci:** add MISE_HTTP_RETRIES alongside UV_HTTP_RETRIES ([40f8166](https://github.com/thewoolleyman/livespec-runtime/commit/40f81669d85554fe5a07ad1224441e14f3992cba))

## [0.18.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.17.0...v0.18.0) (2026-08-09)


### Features

* host spec governance default-block test ([e60b0a9](https://github.com/thewoolleyman/livespec-runtime/commit/e60b0a94588a43fbb1a52193dd4a370df101dc3e))

## [0.17.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.16.1...v0.17.0) (2026-08-06)


### Features

* mitigate github request budget pressure ([c77f2d7](https://github.com/thewoolleyman/livespec-runtime/commit/c77f2d772c8e9b2f6bd934646aadd98a78feabf0))

## [0.16.1](https://github.com/thewoolleyman/livespec-runtime/compare/v0.16.0...v0.16.1) (2026-08-06)


### Bug Fixes

* measure github request budget ([9f28c77](https://github.com/thewoolleyman/livespec-runtime/commit/9f28c77818ddaba454c50068a7e9543617485cf8))

## [0.16.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.15.0...v0.16.0) (2026-08-03)


### Features

* **github-auth:** put the App mint on the IOResult railway ([9b4c518](https://github.com/thewoolleyman/livespec-runtime/commit/9b4c518e49d0b44e9eeb2990e50ee725525dd51b))

## [0.15.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.14.0...v0.15.0) (2026-08-03)


### Features

* **cross-repo:** put the gh provider and its retry wrapper on the railway ([a95ce24](https://github.com/thewoolleyman/livespec-runtime/commit/a95ce24b392e87840e56c78d963dde5c75d7e3ac))

## [0.14.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.13.1...v0.14.0) (2026-08-03)


### Features

* **hygiene-scan:** put the command spawn on the IOResult railway ([cce15a8](https://github.com/thewoolleyman/livespec-runtime/commit/cce15a8aaa34f394a29cbd0759eb1ea144c77904))

## [0.13.1](https://github.com/thewoolleyman/livespec-runtime/compare/v0.13.0...v0.13.1) (2026-08-03)


### Bug Fixes

* **config:** describe the current role-key regime, not selective declaration ([2ab1081](https://github.com/thewoolleyman/livespec-runtime/commit/2ab10810aa9286081667ab37080d08104de04c76))
* **release:** auto-enable release PR merge ([e25aa4b](https://github.com/thewoolleyman/livespec-runtime/commit/e25aa4ba4d895048c60526568fe706b291fe329a))
* route growing jq inputs to stdin in the CI telemetry export ([8aa5137](https://github.com/thewoolleyman/livespec-runtime/commit/8aa5137ae55ff0a850c2be6a4413440ced0c9343))

## [0.13.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.12.0...v0.13.0) (2026-07-22)


### Features

* resolve CLOSED sibling_work_item deps as satisfied via injected lookup ([c91bc1d](https://github.com/thewoolleyman/livespec-runtime/commit/c91bc1de3811771b40b35c120ca8e1ce5867c9f8))

## [0.12.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.11.0...v0.12.0) (2026-07-21)


### Features

* add work item review requirement schema tests ([bbf4980](https://github.com/thewoolleyman/livespec-runtime/commit/bbf49805a3814f10b0901568ad01cae0b6a574b2))


### Bug Fixes

* block readiness on an unresolved sibling work-item dependency ([8eff84b](https://github.com/thewoolleyman/livespec-runtime/commit/8eff84bf3b71141717c66d8dace041d23d7e7eda))

## [0.11.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.10.0...v0.11.0) (2026-07-18)


### Features

* add factory safety attention kind coverage ([2c07540](https://github.com/thewoolleyman/livespec-runtime/commit/2c075405ca0c4b3f850808c2120acb6db35a2aff))


### Bug Fixes

* rename attention residue kind ([ee66ea5](https://github.com/thewoolleyman/livespec-runtime/commit/ee66ea57ff9b2e4c6ac511f3127cffda82e8d9e0))

## [0.10.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.9.2...v0.10.0) (2026-07-18)


### Features

* add factory safety work item coverage ([0274008](https://github.com/thewoolleyman/livespec-runtime/commit/0274008d2b2f9dd1930d23cdefeab21caf2c7252))


### Bug Fixes

* burn down phase1 mechanical check warnings ([b416ef8](https://github.com/thewoolleyman/livespec-runtime/commit/b416ef8cce472b348be112924bd2ac286327a16d))
* **github:** NonCanonicalGithubUrlError catchable as domain type, not ValueError ([43e6645](https://github.com/thewoolleyman/livespec-runtime/commit/43e6645b958f62c0be241bb262f55bd798440da9))
* preserve github url error catchability ([2225526](https://github.com/thewoolleyman/livespec-runtime/commit/22255267436783220bd82b324c47e7dff21eb3e1))
* split hygiene scan file length ([802a5da](https://github.com/thewoolleyman/livespec-runtime/commit/802a5daff9f343be68460269d1c615c656fdf7bc))

## [0.9.2](https://github.com/thewoolleyman/livespec-runtime/compare/v0.9.1...v0.9.2) (2026-07-08)


### Bug Fixes

* add wrapper launch failure diagnostic ([697e45f](https://github.com/thewoolleyman/livespec-runtime/commit/697e45f9807d0a221b0856d37ca86f2cefec7d02))

## [0.9.1](https://github.com/thewoolleyman/livespec-runtime/compare/v0.9.0...v0.9.1) (2026-07-07)


### Bug Fixes

* never flag default-branch worktrees as stale ([18e8527](https://github.com/thewoolleyman/livespec-runtime/commit/18e85270df854bd23f418b36909f5ba0a8db68df))

## [0.9.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.8.0...v0.9.0) (2026-07-07)


### Features

* add attention item schema ([56e58b8](https://github.com/thewoolleyman/livespec-runtime/commit/56e58b8c9a76aebd271e9ce4333a9c0b1a9b0dcb))
* add hygiene scan primitive ([5213a6c](https://github.com/thewoolleyman/livespec-runtime/commit/5213a6cacf1ce21e6fecece0697bb951cea75d2d))
* compose needs-attention items ([889569f](https://github.com/thewoolleyman/livespec-runtime/commit/889569fd48707de8559f8e4770ca73b855036c04))
* flag rebase-merged orphan worktrees in hygiene stale detector ([1b0b3dc](https://github.com/thewoolleyman/livespec-runtime/commit/1b0b3dcae850cc6ffc4852a8b0e02d0789a852db))

## [0.8.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.7.0...v0.8.0) (2026-07-02)


### Features

* **github_auth:** App JWT assembly, PEM normalization + RS256 openssl signer ([4a7527d](https://github.com/thewoolleyman/livespec-runtime/commit/4a7527d0069b5b1e69fccd86f3745e1bac02cf84))
* **github_auth:** caching token provider with pre-expiry transparent re-mint ([f393fa6](https://github.com/thewoolleyman/livespec-runtime/commit/f393fa699eb563d9197dadce8fc51958e5fc7457))
* **github_auth:** env-only fail-closed GithubAppConfig boundary ([bf2f87d](https://github.com/thewoolleyman/livespec-runtime/commit/bf2f87d1fb6ac67c7877b9b21a98ff57de41fdfe))
* **github_auth:** git credential helper answering get with the minted token ([5a0e2e4](https://github.com/thewoolleyman/livespec-runtime/commit/5a0e2e49e5e4e1d15d01a89a6529830fe80556a4))
* **github_auth:** installation-token mint railway over injectable seams ([4f2fd78](https://github.com/thewoolleyman/livespec-runtime/commit/4f2fd78b97624c5e64e6d20944571f67c9bcd775))

## [0.7.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.6.0...v0.7.0) (2026-07-01)


### Features

* carry work item context fields ([647547a](https://github.com/thewoolleyman/livespec-runtime/commit/647547a55a9669e0d1e034cebc9aad58b14dd28a))


### Bug Fixes

* clarify work item context optionality ([5c36c83](https://github.com/thewoolleyman/livespec-runtime/commit/5c36c830f105cfa39732d6ff8cfefc6407b6ce42))

## [0.6.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.5.0...v0.6.0) (2026-07-01)


### Features

* **credentials:** add pure decide_credentials self-heal decision ([b70c8c0](https://github.com/thewoolleyman/livespec-runtime/commit/b70c8c03e09da7937eca0db62484c63aa7d660b4))

## [0.5.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.4.0...v0.5.0) (2026-06-29)


### Features

* **work_items:** lifecycle lane authority (lane_of/is_item_ready/ready_sort_key) ([4cda557](https://github.com/thewoolleyman/livespec-runtime/commit/4cda557bc36aef5d27e22f05774a8295db9afbe9))
* **work_items:** rank fractional-index wrapper (key_between/n_keys_between/BOTTOM_SENTINEL) ([976cf86](https://github.com/thewoolleyman/livespec-runtime/commit/976cf8630caef1fbb5231321cc536d695506f804))
* **work_items:** WorkItem 20-field schema (7-state status, +rank, -priority, policy fields) ([84173e6](https://github.com/thewoolleyman/livespec-runtime/commit/84173e613408927c9a0aa8b38bb598347c7ebcd7))

## [0.4.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.3.1...v0.4.0) (2026-06-20)


### Features

* extract shared WorkItem store surface into livespec_runtime.work_items (livespec-4jsi) ([dccc818](https://github.com/thewoolleyman/livespec-runtime/commit/dccc8181e843a02196dbb86c9a47e0bce833f5d9))

## [0.3.1](https://github.com/thewoolleyman/livespec-runtime/compare/v0.3.0...v0.3.1) (2026-06-12)


### Bug Fixes

* **github:** detect 404 via structured HTTP 404 marker, not substring (li-y2hd44) ([6a0f705](https://github.com/thewoolleyman/livespec-runtime/commit/6a0f7059c9237542292d5d857390dd6a02a032be))

## [0.3.0](https://github.com/thewoolleyman/livespec-runtime/compare/v0.2.1...v0.3.0) (2026-05-25)


### Features

* **workflows:** drop cross-repo coordination shim workflows ([#5](https://github.com/thewoolleyman/livespec-runtime/issues/5)) ([bcc646e](https://github.com/thewoolleyman/livespec-runtime/commit/bcc646e27fbe1db5f15c2f973d1a840850158983))

## [0.2.1](https://github.com/thewoolleyman/livespec-runtime/compare/v0.2.0...v0.2.1) (2026-05-24)


### Bug Fixes

* **typing:** add `py.typed` marker for PEP 561 compliance so consumers' pyright/mypy can pick up inline type annotations without `useLibraryCodeForTypes`.


## 0.2.0 (2026-05-24)


### Features

* **cross_repo:** types, providers/github, retry, resolve — cross-repo dependency resolution surface (li-aclzfe).
* **spec:** seed livespec-runtime SPECIFICATION/ (li-ufvfmb).


## 0.1.0 (2026-05-23)


### Features

* **scaffold:** hand-author livespec-runtime v0.1.0 scaffold (li-ufvfmb).
