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
        self.rule_name = "useMethodOfPRNG.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))
        if not os.path.exists(self.rule_path):
            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

    def verify(self):
        from quark.script import findMethodInAPK

        result_list = []
        methodsFound = []
        for target in self.target_method_list:
            methodsFound += findMethodInAPK(self.apk_path, target)

        for setHashAlgo in methodsFound:
            algoName = setHashAlgo.getArguments()[0].replace("-", "")

            if any(keyword in algoName for keyword in self.hash_keyword_list):
                finding = f"Use of Weak Hash is detected with {algoName} in method, {setHashAlgo.fullName}"
                result_list.append(finding)

        return {"CWE328": result_list}
