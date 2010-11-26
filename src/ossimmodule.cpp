#include <Python.h>
#include <ossim/init/ossimInit.h>
#include <ossim/base/ossimArgumentParser.h>
#include <ossim/base/ossimApplicationUsage.h>
#include <ossim/base/ossimGeoidManager.h>
#include <ossim/elevation/ossimElevManager.h>

#include <cstdlib>
#include <iomanip>


// ripped from ossim-height
// FIXME: add correct headers (licence & friends)
static PyObject* 
get_elevation(double lat, double lon){
  ossimGpt gpt;
  gpt.latd(lat);
  gpt.lond(lon);

  ossim_float64 hgtAboveMsl       = ossimElevManager::instance()->
    getHeightAboveMSL(gpt);

  ossim_float64 hgtAboveEllipsoid = ossimElevManager::instance()->
    getHeightAboveEllipsoid(gpt);

  ossim_float64 geoidOffset       = ossimGeoidManager::instance()->
    offsetFromEllipsoid(gpt);

  ossim_float64 mslOffset       = 0.0;
   
  if(ossim::isnan(hgtAboveEllipsoid)||ossim::isnan(hgtAboveMsl)) {
    mslOffset = ossim::nan();
  } else {
    mslOffset = hgtAboveEllipsoid - hgtAboveMsl;
  }

#if 1 /* Tmp until this functionality is added back. */
  /* kept from original ossim code */
  std::vector<ossimFilename> cellList;
  ossimElevManager::instance()->getOpenCellList(cellList);
#endif

  if (ossim::isnan(hgtAboveEllipsoid) || ossim::isnan(hgtAboveMsl))
    Py_RETURN_NONE;

  PyObject *ret = Py_BuildValue("ff", hgtAboveMsl, hgtAboveEllipsoid);
  return ret;
}



static PyObject *
ossim_init(PyObject *self, PyObject *args)
{
  char *pref_file;

  if (!PyArg_ParseTuple(args, "s", &pref_file))
        return NULL;

  char *argv[] = {"ossim-height", "-P", pref_file};
  int argc = 3;

  ossimArgumentParser argumentParser(&argc, argv);

  ossimInit::instance()->addOptions(argumentParser);

  ossimInit::instance()->initialize(argumentParser);

  argumentParser.getApplicationUsage()->setApplicationName(
    argumentParser.getApplicationName());
  
  Py_RETURN_NONE;
}

static PyObject *
ossim_height(PyObject *self, PyObject *args)
{
  float lat,lon;
  //  char lat_s[10], lon_s[10];

  //  char *pref_file;

  // memset(lat_s, 0, 10);
  // memset(lon_s, 0, 10);

  if (!PyArg_ParseTuple(args, "ff", &lat, &lon))
        return NULL;

  // snprintf(lat_s, 10, "%.6f", lat);
  // snprintf(lon_s, 10, "%.6f", lon);
  
  return get_elevation(lat, lon);
}


static PyMethodDef OssimMethods[] = {
  {"height",  ossim_height, METH_VARARGS,
   "Give the height of a given point."},
  {"init",  ossim_init, METH_VARARGS,
   "Initialize the OSSIM library."},
  {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initossim(void)
{
  (void) Py_InitModule("ossim", OssimMethods);
}
