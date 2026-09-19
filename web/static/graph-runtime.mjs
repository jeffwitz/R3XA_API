import {buildDot, buildGraphModel, formatNodeLabel} from "./graph-core.mjs";

const WASM_ASSET = "./graphviz-12.2.1.wasm";
const WASI_SUCCESS = 0;
const WASI_EBADF = 8;
const WASI_ENOENT = 44;

const decoder = new TextDecoder();
const encoder = new TextEncoder();

const memoryView = (state) => new DataView(state.instance.exports.memory.buffer);
const memoryBytes = (state) => new Uint8Array(state.instance.exports.memory.buffer);

const writeU32 = (state, pointer, value) => memoryView(state).setUint32(pointer, value >>> 0, true);

const writeU64 = (state, pointer, value) => memoryView(state).setBigUint64(pointer, BigInt(value), true);

const readU32 = (state, pointer) => memoryView(state).getUint32(pointer, true);

const readBytes = (state, pointer, length) => memoryBytes(state).slice(pointer, pointer + length);

const writeBytes = (state, pointer, bytes) => memoryBytes(state).set(bytes, pointer);

const readString = (state, pointer, length) => decoder.decode(readBytes(state, pointer, length));

const createWasiImports = (state) => {
  const argv = ["r3xa-graphviz"];
  const argvBytes = argv.map((value) => encoder.encode(value));
  return {
    wasi_snapshot_preview1: {
      args_get: (argvPointer, argvBufferPointer) => {
        let bufferPointer = argvBufferPointer;
        argvBytes.forEach((bytes, index) => {
          writeU32(state, argvPointer + index * 4, bufferPointer);
          writeBytes(state, bufferPointer, bytes);
          bufferPointer += bytes.length;
          memoryBytes(state)[bufferPointer++] = 0;
        });
        return WASI_SUCCESS;
      },
      args_sizes_get: (argcPointer, argvBufferSizePointer) => {
        writeU32(state, argcPointer, argv.length);
        writeU32(state, argvBufferSizePointer, argvBytes.reduce((sum, bytes) => sum + bytes.length + 1, 0));
        return WASI_SUCCESS;
      },
      environ_get: () => WASI_SUCCESS,
      environ_sizes_get: (countPointer, sizePointer) => {
        writeU32(state, countPointer, 0);
        writeU32(state, sizePointer, 0);
        return WASI_SUCCESS;
      },
      fd_close: () => WASI_SUCCESS,
      fd_fdstat_get: (fd, statPointer) => {
        if (![0, 1, 2].includes(fd)) return WASI_EBADF;
        const view = memoryView(state);
        view.setUint8(statPointer, 2);
        view.setUint16(statPointer + 2, 0, true);
        writeU64(state, statPointer + 8, 0);
        writeU64(state, statPointer + 16, 0);
        return WASI_SUCCESS;
      },
      fd_fdstat_set_flags: () => WASI_SUCCESS,
      fd_filestat_get: (fd, statPointer) => {
        if (![0, 1, 2].includes(fd)) return WASI_EBADF;
        memoryBytes(state).fill(0, statPointer, statPointer + 64);
        return WASI_SUCCESS;
      },
      fd_prestat_get: () => WASI_ENOENT,
      fd_prestat_dir_name: () => WASI_ENOENT,
      fd_read: (fd, _, __, resultPointer) => {
        if (![0, 1, 2].includes(fd)) return WASI_EBADF;
        writeU32(state, resultPointer, 0);
        return WASI_SUCCESS;
      },
      fd_seek: (fd, _, __, resultPointer) => {
        if (![0, 1, 2].includes(fd)) return WASI_EBADF;
        writeU64(state, resultPointer, 0);
        return WASI_SUCCESS;
      },
      fd_write: (fd, iovsPointer, iovsLength, resultPointer) => {
        if (![1, 2].includes(fd)) return WASI_EBADF;
        let written = 0;
        for (let index = 0; index < iovsLength; index += 1) {
          const pointer = iovsPointer + index * 8;
          const dataPointer = readU32(state, pointer);
          const dataLength = readU32(state, pointer + 4);
          written += dataLength;
          if (dataLength && fd === 2) console.error(readString(state, dataPointer, dataLength));
        }
        writeU32(state, resultPointer, written);
        return WASI_SUCCESS;
      },
      path_filestat_get: () => WASI_ENOENT,
      path_open: () => WASI_ENOENT,
      proc_exit: (code) => {
        throw new Error(`Graphviz WebAssembly exited with status ${code}`);
      },
      random_get: (pointer, length) => {
        const bytes = memoryBytes(state).subarray(pointer, pointer + length);
        crypto.getRandomValues(bytes);
        return WASI_SUCCESS;
      },
    },
  };
};

const getGraphviz = () => {
  if (!getGraphviz.promise) {
    getGraphviz.promise = (async () => {
      const response = await fetch(new URL(WASM_ASSET, import.meta.url));
      if (!response.ok) throw new Error(`Unable to load ${WASM_ASSET} (${response.status})`);
      const bytes = await response.arrayBuffer();
      const state = {instance: null};
      const result = await WebAssembly.instantiate(bytes, createWasiImports(state));
      state.instance = result.instance;
      return state;
    })();
  }
  return getGraphviz.promise;
};

const readCString = (state, pointer) => {
  const bytes = memoryBytes(state);
  let end = pointer;
  while (end < bytes.length && bytes[end] !== 0) end += 1;
  return decoder.decode(bytes.slice(pointer, end));
};

const renderDot = async (dot) => {
  const state = await getGraphviz();
  const {memory, malloc, free, r3xa_graphviz_render: render, r3xa_graphviz_last_error: lastError} = state.instance.exports;
  const source = encoder.encode(dot);
  const sourcePointer = malloc(source.length + 1);
  const lengthPointer = malloc(4);
  writeBytes(state, sourcePointer, source);
  memoryBytes(state)[sourcePointer + source.length] = 0;
  try {
    const resultPointer = render(sourcePointer, source.length, lengthPointer);
    if (!resultPointer) {
      throw new Error(readCString(state, lastError()) || "unknown Graphviz WebAssembly error");
    }
    const resultLength = readU32(state, lengthPointer);
    const result = decoder.decode(readBytes(state, resultPointer, resultLength));
    free(resultPointer);
    return result;
  } finally {
    free(sourcePointer);
    free(lengthPointer);
  }
};

export const renderGraph = async (document, options = {}, styles) => {
  const paletteStyles = styles?.[options.palette || "document"] || styles?.document || styles;
  const dot = buildDot(document, options, paletteStyles);
  return renderDot(dot);
};

export {buildDot, buildGraphModel, formatNodeLabel};
