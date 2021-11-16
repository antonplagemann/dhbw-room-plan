module.exports = {
    'env': {
        'browser': true,
        'es6': true
    },
    'extends': [
        'eslint:recommended',
        'plugin:vue/recommended'
    ],
    'parserOptions': {
        'ecmaVersion': 2020,
        'sourceType': 'module'
    },
    'plugins': ['vue'],
    'rules': {
        "vue/html-indent": ["error", 2, { "attribute": 2, "closeBracket": 0 }],
        "vue/html-closing-bracket-newline": [
            "error",
            {
                "singleline": "never",
                "multiline": "never"
            }
        ],
        "vue/singleline-html-element-content-newline": ["error", {
            "ignoreWhenNoAttributes": true,
            "ignoreWhenEmpty": true,
            "ignores": ["pre", "textarea", "p", "span", "li"]
        }],
        "vue/max-attributes-per-line": ["error", {
            "singleline": 1,
            "multiline": {
                "max": 1,
                "allowFirstLine": true
            }
        }]
    }
};
