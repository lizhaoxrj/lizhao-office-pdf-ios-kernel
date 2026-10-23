lizhao-office-pdf-ios-kernel

本仓库提供固定范围的 LibreOffice iOS 离线文档转 PDF 内核构建候选、移植补丁及 C ABI 封装，不包含完整 lizhao-office-pdf UTS 插件或业务项目。
目标格式为 DOC、DOCX、PPT、PPTX。当前尚未完成完整 Apple 编译、资源集成、离线资格和真机功能验收；不得将候选描述为可用发行版本。

源码与构建
kernel-source.json 包含已公开的 28 项纯文本内核源码、测试和构建文件。restore-source.py 校验精确白名单、长度和 SHA-256 后恢复 native-kernels/lizhao-office-pdf-ios/，拒绝覆盖已有目录。
本地查看：python3 restore-source.py --manifest kernel-source.json --destination .
GitHub Actions 工作流位于 .github/workflows/office-pdf-ios.yml，仅允许 workflow_dispatch；mode=probe 探测环境，mode=build 执行真实构建。使用标准 macos-15-intel，凭据不保留，日志和候选产物保留 1 天。
内嵌 ci/README.md 记录原私有 CI 的历史说明；本公开仓库沿用同一可核验源码，不导入旧仓库历史或完整插件。

来源与许可边界
上游固定为 LibreOffice libreoffice-26.2.6.3，commit 8221e31b3ac356a1623c672912a3d2b492f7e3d1。
上游源码、片段及对应修改保留其原有版权和文件许可声明。官方源码与许可：
https://github.com/LibreOffice/core/tree/8221e31b3ac356a1623c672912a3d2b492f7e3d1
https://raw.githubusercontent.com/LibreOffice/core/8221e31b3ac356a1623c672912a3d2b492f7e3d1/COPYING.MPL
https://raw.githubusercontent.com/LibreOffice/core/8221e31b3ac356a1623c672912a3d2b492f7e3d1/COPYING.LGPL
第三方依赖保留各自声明。本说明不为作者独立封装及构建代码另行新增整体许可证，也不授予未公开完整插件的使用权。
实际二进制和资源分发前仍须核对所含组件、字体及对应许可和源码提供要求；当前候选构建不能替代该清单或功能验收。
