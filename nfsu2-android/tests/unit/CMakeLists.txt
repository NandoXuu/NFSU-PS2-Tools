set(NFSU2_TESTS test_fixed_timestep test_mesh test_texture test_wav)

foreach(t ${NFSU2_TESTS})
    add_executable(${t} ${t}.cpp)
    target_link_libraries(${t} PRIVATE nfsu2_core)
    target_compile_options(${t} PRIVATE -Wall -Wextra)
    add_test(NAME ${t} COMMAND ${t})
endforeach()

# Teste opcional contra dados reais convertidos (definir NFSU2_REAL_ASSETS=<pasta>).
add_executable(test_real_assets test_real_assets.cpp)
target_link_libraries(test_real_assets PRIVATE nfsu2_core)
add_test(NAME test_real_assets COMMAND test_real_assets)
