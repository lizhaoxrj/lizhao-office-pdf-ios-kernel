lizhao-office-pdf-ios-kernel

本公开仓库仅含LibreOffice iOS内核移植、C ABI封装、公开合成夹具与构建材料，不含完整UTS插件、私有Bridge/UTS/生成Swift、客户文档、凭据或证书。

固定生产者候选为完整构建 #12 / run40131160579 / source5d8083b9e6aeba055d0ae58761271e5341f04bb2。五阶段已成功，真实arm64/iPhoneOS/最低14.5最终force_load链接及资源原件已核；内核仍acceptanceOnly/testOnly，available=false、strictOffline=false。这些构建证据不代表已执行转换、私有宿主联编、严格离线或设备验收。

kernel-source.json恰含39项白名单UTF-8源码/文本材料；restore-source.py在长度、SHA与路径检查后恢复native-kernels/lizhao-office-pdf-ios/，拒绝覆盖。恢复器必须使用本次受审原件，不能以远端JSON扩大白名单。本地查看命令：python3 restore-source.py --manifest kernel-source.json --destination .

.github/workflows/office-pdf-ios.yml是保留原件的主构建流程；本次main/build已经运行一次，不再触发或重建。独立office-pdf-ios-export.yml仅供本线程已批准并已完成的一次固定两文件短期下载例外，例外不扩成常规二进制artifact策略。

新增.github/workflows/office-pdf-ios-harness.yml只允许手工触发，标准免费macos-15-intel、contents:read、原串行组。它精确恢复固定producer的final缓存，cache-hit与两文件/producer/完整2583成员和2410文件身份必须通过，无前缀回退、cache-save/delete或make。消费者commit/run/attempt另行记录，不能冒充producer。通过本次源码/工具/远端审查后仅发起独立harness一次。

公开Swift入口直接import OfficePdfKernel，并真实引用ProbeJSON、生产ConvertJSON拒绝负对照、AcceptanceConvertJSON、FreeString；编译-Onone对象核四引用，保留原force_load及12framework/5系统库，增加PDFKit。真实Apple编译、链接、vtool和完整unsigned App形状资源staging仅证明相应构建层，不执行iPhoneOS二进制、不签证或安装。输入提取后固定实际fs身份，资源staging后编译前和链接后必须以同一dev/inode/mode/nlink/size/mtime_ns/ctime_ns映射及全SHA/路径核对；归档ns与文件系统精度边界分别报告。

harness只上传经过封存的有界JSON/log：单文件32MiB、总128MiB且留1MiB元数据余量，无framework、payload、exe、App或IPA大artifact。原候选与缓存保留；主ICU与完整资源bundle分别staging到App根，不把静态framework作为动态库embed。当前没有设备运行或私有SwiftCompile证据，harness也不是可安装基座。

acceptance/notices-source.json包含109项内部unsigned验收许可/来源材料：107份原件与2份显式脱敏派生索引，逐项长度/SHA/base64与来源可核。OpenSymbol许可出处、字体源包对应、其余对象来源、配置化LICENSE、对应源码和静态重链接交付材料等六项外发缺口完整保留；redistributionApproved=false，不能把本材料或URL当完整再分发资格。

详细合同与各阶段边界在恢复后的native-kernels/lizhao-office-pdf-ios/ci/README.md。实际结果必须读取对应run/attempt的官方原始日志和回执；源码检查、Windows测试、cache命中及目录呈App形状均不等于Apple编译成功或运行成功。
