"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.postReceiveActionBinaryData = void 0;
exports.preSendActionCustonBody = preSendActionCustonBody;
async function preSendActionCustonBody(requestOptions) {
    const { customBody } = requestOptions.body;
    if (typeof requestOptions.body === 'object' && typeof customBody === 'object') {
        requestOptions.body = {
            ...requestOptions.body,
            ...customBody,
        };
        delete requestOptions.body.customBody;
    }
    return Promise.resolve(requestOptions);
}
function getResponseContentType(response) {
    return response.headers['content-type'];
}
function getFileTypeFromContentType(contentType) {
    const type = contentType.split(';')[0].trim();
    if (type.includes('/')) {
        return type.split('/')[0];
    }
    return type;
}
function getFileExtensionFromContentType(contentType) {
    const type = contentType.split(';')[0].trim();
    if (typeof type === 'string' && type.includes('/')) {
        return type.split('/')[1];
    }
    return type;
}
function isBinaryResponse(contentType) {
    const textContentTypes = [
        /application\/json/,
        /application\/xml/,
        /application\/xhtml\+xml/,
        /application\/atom\+xml/,
        /application\/rss\+xml/,
        /application\/rdf\+xml/,
        /application\/ld\+json/,
        /application\/pdf/,
        /application\/ld\+json/,
        /^text\//,
    ];
    return !textContentTypes.some((regex) => regex.test(contentType));
}
const postReceiveActionBinaryData = async function postReceiveActionBinaryData(items, response) {
    const contentType = getResponseContentType(response);
    const isBinary = isBinaryResponse(contentType);
    const { binary } = items[0];
    if (isBinary && binary && binary.data && binary.data.mimeType === 'text/plain') {
        const data = binary.data;
        data.data = Buffer.from(response.body, 'binary');
        data.mimeType = contentType;
        data.fileType = getFileTypeFromContentType(contentType);
        data.fileExtension = getFileExtensionFromContentType(contentType);
    }
    if (binary && binary.data && !binary.data.fileName) {
        binary.data.fileName = `data.${getFileExtensionFromContentType(contentType)}`;
    }
    return items;
};
exports.postReceiveActionBinaryData = postReceiveActionBinaryData;
//# sourceMappingURL=hooks.js.map