# Changelog

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
