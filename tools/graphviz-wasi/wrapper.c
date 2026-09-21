#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include <gvc/gvc.h>
#include <gvc/gvplugin.h>

extern gvplugin_library_t gvplugin_core_LTX_library;
extern gvplugin_library_t gvplugin_dot_layout_LTX_library;
extern gvplugin_library_t gvplugin_vt_LTX_library;

static lt_symlist_t r3xa_builtins[] = {
    {"gvplugin_dot_layout_LTX_library", &gvplugin_dot_layout_LTX_library},
    {"gvplugin_core_LTX_library", &gvplugin_core_LTX_library},
    {"gvplugin_vt_LTX_library", &gvplugin_vt_LTX_library},
    {0, 0},
};

static char r3xa_last_error[512];

static void r3xa_set_error(const char *message) {
    if (message == NULL) {
        message = "unknown Graphviz error";
    }
    strncpy(r3xa_last_error, message, sizeof(r3xa_last_error) - 1);
    r3xa_last_error[sizeof(r3xa_last_error) - 1] = '\0';
}

const char *r3xa_graphviz_last_error(void) {
    return r3xa_last_error;
}

void r3xa_graphviz_free(void *pointer) {
    free(pointer);
}

char *r3xa_graphviz_render(
    const char *dot_source,
    uint32_t dot_length,
    uint32_t *svg_length
) {
    GVC_t *context = NULL;
    graph_t *graph = NULL;
    char *svg = NULL;
    char *result = NULL;
    unsigned int rendered_length = 0;

    r3xa_last_error[0] = '\0';
    if (dot_source == NULL || svg_length == NULL) {
        r3xa_set_error("invalid null input");
        return NULL;
    }

    char *source = malloc((size_t)dot_length + 1);
    if (source == NULL) {
        r3xa_set_error("unable to allocate DOT input");
        return NULL;
    }
    memcpy(source, dot_source, dot_length);
    source[dot_length] = '\0';

    context = gvContextPlugins(r3xa_builtins, 0);
    if (context == NULL) {
        r3xa_set_error("unable to create Graphviz context");
        free(source);
        return NULL;
    }

    graph = agmemread(source);
    free(source);
    if (graph == NULL) {
        r3xa_set_error("Graphviz could not parse DOT input");
        gvFreeContext(context);
        return NULL;
    }

    if (gvLayout(context, graph, "dot") != 0) {
        r3xa_set_error("Graphviz dot layout failed");
        agclose(graph);
        gvFreeContext(context);
        return NULL;
    }

    if (gvRenderData(context, graph, "svg", &svg, &rendered_length) != 0 || svg == NULL) {
        r3xa_set_error("Graphviz SVG rendering failed");
        gvFreeLayout(context, graph);
        agclose(graph);
        gvFreeContext(context);
        return NULL;
    }

    result = malloc(rendered_length);
    if (result == NULL) {
        r3xa_set_error("unable to allocate SVG output");
        gvFreeRenderData(svg);
        gvFreeLayout(context, graph);
        agclose(graph);
        gvFreeContext(context);
        return NULL;
    }
    memcpy(result, svg, rendered_length);
    *svg_length = rendered_length;

    gvFreeRenderData(svg);
    gvFreeLayout(context, graph);
    agclose(graph);
    gvFreeContext(context);
    return result;
}
