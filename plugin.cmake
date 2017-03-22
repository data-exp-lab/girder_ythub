add_python_test(basic PLUGIN wholetale)
add_python_test(dataone PLUGIN wholetale)
add_python_test(recipe PLUGIN wholetale)
add_python_test(image PLUGIN wholetale)
add_python_style_test(python_static_analysis_wholetale
                      "${PROJECT_SOURCE_DIR}/plugins/wholetale/server")
