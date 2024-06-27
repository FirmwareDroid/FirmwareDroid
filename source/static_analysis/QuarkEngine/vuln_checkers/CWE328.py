import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE328(VulnCheck):
    target_method_list = [
        [
            "Ljava/security/MessageDigest;",
            "getInstance",
            "(Ljava/lang/String;)Ljava/security/MessageDigest;",
        ],
        [
            "Ljavax/crypto/SecretKeyFactory;",
            "getInstance",
            "(Ljava/lang/String;)Ljavax/crypto/SecretKeyFactory;",
        ],
    ]

    hash_keyword_list = [
        "MD2",
        "MD4",
        "MD5",
        "PANAMA",
        "SHA0",
        "SHA1",
        "HAVAL128",
        "RIPEMD128",
    ]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path

    def verify(self):
        from quark.script import findMethodInAPK

        result_list = []
        methodsFound = []
        for target in self.target_method_list:
            methodsFound += findMethodInAPK(self.apk_path, target)

        for setHashAlgo in methodsFound:
            argument_list = setHashAlgo.getArguments()
            if argument_list and len(argument_list) >= 1:
                algoName = argument_list[0].replace("-", "")

                if any(keyword in algoName for keyword in self.hash_keyword_list):
                    result_list.append(f"Use of Weak Hash is detected with {algoName} in method, "
                                       f"{setHashAlgo.fullName}")

        return {"CWE328": result_list}
