@main def main(name : String): Unit = {
    importCpg(name)
    def methods1 = cpg.typeDecl.filter{x => x.method.name.l.contains("__set")}.name.l
    val x32 = (name, "32_set_overloading_iall", cpg.call("NEW").argument.filter{x => methods1.contains(x.code.toLowerCase)}.size);
    println(x32)
    delete;
} 