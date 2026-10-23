lizhao-office-pdf-ios-kernel

本仓库提供固定范围的 LibreOffice iOS 离线文档转 PDF 内核构建候选、移植补丁及 C ABI 封装，不包含完整 lizhao-office-pdf UTS 插件或业务项目。
目标格式为 DOC、DOCX、PPT、PPTX。当前尚未完成完整 Apple 编译、资源集成、离线资格和真机功能验收；不得将候选描述为可用发行版本。

源码与构建
kernel-source.json 仅包含精确白名单内的纯文本内核源码、测试和构建文件。restore-source.py 校验白名单、长度和 SHA-256 后恢复 native-kernels/lizhao-office-pdf-ios/，拒绝覆盖已有目录。
本地查看：python3 restore-source.py --manifest kernel-source.json --destination .
GitHub Actions 工作流位于 .github/workflows/office-pdf-ios.yml，仅允许 workflow_dispatch；mode=probe 探测环境，mode=build 顺序执行 tools、vcl、sd、sw、final 五个真实构建阶段。
阶段目标为 cross-toolset、vcl.allbuild、sd.allbuild、sw.allbuild、build，保留最终完整构建与资源封装，不裁剪格式、模块或注册表。使用标准 macos-15-intel，凭据不保留，无证书或付费 runner。
成功阶段通过精确身份、前阶段 SHA 和安全归档检查后才能续编；单缓存连同清单及预留开销不超过 4GiB，不调整仓库默认缓存或付费限额。缺失、超限或身份不符立即失败，不静默重建。
artifact 仅保留有界 JSON 和原始日志 1 天，不上传构建树或候选大二进制。最终候选单独保存于有界缓存，清单、SHA、体积和缓存键见 CANDIDATE-INVENTORY.json、CANDIDATE-CACHE.json；保存后必须精确查询命中。
缓存会受服务的默认淘汰规则影响，不保证永久保存。最终候选的免费取回方式仍须按实际产物核对；阶段成功或缓存命中不等于插件可用、离线资格或真机验收通过。
内嵌 native-kernels/lizhao-office-pdf-ios/ci/README.md 记录构建细节及历史说明；本公开仓库不导入旧私有仓库历史或完整插件。

来源与许可边界
上游固定为 LibreOffice libreoffice-26.2.6.3，commit 8221e31b3ac356a1623c672912a3d2b492f7e3d1。
上游源码、片段及对应修改保留其原有版权和文件许可声明。官方源码与许可：
https://github.com/LibreOffice/core/tree/8221e31b3ac356a1623c672912a3d2b492f7e3d1
https://raw.githubusercontent.com/LibreOffice/core/8221e31b3ac356a1623c672912a3d2b492f7e3d1/COPYING.MPL
https://raw.githubusercontent.com/LibreOffice/core/8221e31b3ac356a1623c672912a3d2b492f7e3d1/COPYING.LGPL
第三方依赖保留各自声明。本说明不为作者独立封装及构建代码另行新增整体许可证，也不授予未公开完整插件的使用权。
实际二进制和资源分发前仍须核对所含组件、字体及对应许可和源码提供要求；当前候选构建不能替代该清单或功能验收。
