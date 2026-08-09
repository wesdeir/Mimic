#include "app_info.h"

#include "version.h"

namespace mimic::app {

const char* appTitle() {
    return "Mimic";
}

const char* appVersion() {
    return mimic::core::versionString();
}

} // namespace mimic::app
