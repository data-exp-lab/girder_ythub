add_python_test(frontend PLUGIN ythub)
add_python_test(notebook PLUGIN ythub)
add_python_test(heartbeat PLUGIN ythub)
add_python_test(ythub PLUGIN ythub)
add_python_style_test(python_static_analysis_ythub
                      "${PROJECT_SOURCE_DIR}/plugins/ythub/server")
