#!/usr/bin/env python
# fastqc 0.0.1
# Generated by dx-app-wizard.
#
# Parallelized execution pattern: Your app will generate multiple jobs
# to perform some computation in parallel, followed by a final
# "postprocess" stage that will perform any additional computations as
# necessary.
#
# See https://wiki.dnanexus.com/Developer-Portal for documentation and
# tutorials on how to modify this file.
#
# DNAnexus Python Bindings (dxpy) documentation:
#   http://autodoc.dnanexus.com/bindings/python/current/

import sys, os, subprocess, json, requests, shlex, urlparse, logging
from datetime import datetime
import dxpy

print sys.path
print subprocess.check_output(['ls','-l'])
print subprocess.check_output(['ls','dxencode','-l']) # should contain keypairs

#from dxencode import dxencode as dxencode
from dxencode import dx as dx
from dxencode import encd as encd

logger = logging.getLogger("Applet")

'''
        {
            "dataset": "ENCSR000ACY",
            "file_format": "fastq",
            "file_size": os.path.getsize(path),
            "md5sum": md5sum.hexdigest(),
            "output_type": "raw data",
            "submitted_file_name": path,
            "lab": my_lab,
            "award": my_award
        }
'''
root_dir = os.environ.get('DX_FS_ROOT') or ""
DATA = root_dir+"/opt/data/"
encValData  = DATA+'encValData'
validate_map = {
    'bam': ['-type=bam'],
    'bed': ['-type=bed6+'],  # if this fails we will drop to bed3+
    'bedLogR': ['-type=bigBed9+1', '-as=%s/as/bedLogR.as' % encValData],
    'bed_bedLogR': ['-type=bed9+1', '-as=%s/as/bedLogR.as' % encValData],
    'bedMethyl': ['-type=bigBed9+2', '-as=%s/as/bedMethyl.as' % encValData],
    'bed_bedMethyl': ['-type=bed9+2', '-as=%s/as/bedMethyl.as' % encValData],
    'bigBed': ['-type=bigBed6+'],  # if this fails we will drop to bigBed3+
    'bigWig': ['-type=bigWig'],
    'broadPeak': ['-type=bigBed6+3', '-as=%s/as/broadPeak.as' % encValData],
    'bed_broadPeak': ['-type=bed6+3', '-as=%s/as/broadPeak.as' % encValData],
    'fasta': ['-type=fasta'],
    'fastq': ['-type=fastq'],
    'gtf': None,
    'idat': ['-type=idat'],
    'narrowPeak': ['-type=bigBed6+4', '-as=%s/as/narrowPeak.as' % encValData],
    'bed_narrowPeak': ['-type=bed6+4', '-as=%s/as/narrowPeak.as' % encValData],
    'rcc': ['-type=rcc'],
    'tar': None,
    'tsv': None,
    '2bit': None,
    'csfasta': ['-type=csfasta'],
    'csqual': ['-type=csqual'],
    'bedRnaElements': ['-type=bed6+3', '-as=%s/as/bedRnaElements.as' % encValData],
    'CEL': None,
}

def validate(filename, file_meta):
    # Change the following to process whatever input this stage
    # receives.  You may also want to copy and paste the logic to download
    # and upload files here as well if this stage receives file input
    # and/or makes file output.

    logger.debug(file_meta)

    logger.debug("Run Validate Files on %s" % filename)
    validate_args = validate_map.get(file_meta['file_format'])
    assembly = file_meta.get('assembly')

    if file_meta['file_format'] == 'bam' and file_meta.get('output_type','') == 'transcriptome alignments':
        chromInfo = ['-chromInfo=%s/%s/%s/chrom.sizes' % (encValData, assembly, file_meta['genome_annotation'])]
    elif assembly:
        chromInfo = ['-chromInfo=%s/%s/chrom.sizes' % (encValData, assembly)]
    else:
        # not sure this is a sensible default
        chromInfo = ['-chromInfo=%s/hg19/chrom.sizes' % encValData]

    print subprocess.check_output(['ls','-l'])
    valid = "Not validated yet"
    if validate_args is not None:
        logger.debug(("Validating file."))
        validation_command = ['validateFiles'] + validate_args + chromInfo + ['-doReport'] + [filename]
        try:
            logger.debug( " ".join(validation_command) )
            valid = subprocess.check_output(validation_command)
        except subprocess.CalledProcessError as e:
            pass
            logger.debug((e.output))

    else:
        return {
            "validation": "Not Run for type: %s" % file_meta['file_format']
        }

    logger.debug(valid)
    print subprocess.check_output(['ls','-l'])
    logger.debug("Upload result")
    report_dxfile = dxpy.upload_local_file("%s.report" % filename)
    logger.debug(report_dxfile)
    ## is_valid == 'Error count 0'
    return {
        "report": report_dxfile,
        "validation": valid
    }

@dxpy.entry_point("main")
def main(pipe_file, file_meta, key=None, debug=False, skipvalidate=True):

    # The following line(s) initialize your data object inputs on the platform
    # into dxpy.DXDataObject instances that you can start using immediately.

    #files = [dxpy.DXFile(item) for item in files]

    # The following line(s) download your file inputs to the local file system
    # using variable names for the filenames.

    #for i, f in enumerate(files):
    #    dxpy.download_dxfile(f.get_id(), "files-" + str(i))

    # Split your work into parallel tasks.  As an example, the
    # following generates 10 subjobs running with the same dummy
    # input.

    encd.logger = logging.getLogger("Applet.dxe")
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    (AUTHID,AUTHPW,SERVER) = encd.processkey(key)

    f_des = dxpy.describe(pipe_file)
    filename = f_des['name']
    fid = f_des['id']
    folder = dxpy.DXFile(fid, project=dxpy.PROJECT_CONTEXT_ID).folder
    logger.info("* Downloading file from dx to local...")
    start = datetime.now()
    dx_file = dxpy.download_dxfile(pipe_file, filename)
    end = datetime.now()
    duration = end - start
    logger.info("* Download in %.2f seconds" % duration.seconds)

    if filename.endswith('.bed') or filename.endswith('.gff'):
        subprocess.check_call(['gzip',filename])
        filename = filename + '.gz'

    # gathering metadata
    file_meta['submitted_file_name'] = "%s/%s" % (folder, filename)
    file_meta['md5sum'] = dx.calc_md5(filename).hexdigest()
    file_meta['file_size'] = os.path.getsize(filename)
    if "aliases" not in file_meta:
        file_meta["aliases"] = []
    file_meta["aliases"].append("dnanexus:"+fid)
    if file_meta.get('accession') != None:
        file_meta["status"] = "upload failed" # Can only repost to same accession if status is upload failed.

    if not skipvalidate:
        logger.info("* Validating: %s (%s)" % (filename, folder))
        start = datetime.now()
        v = validate(filename, file_meta)
        end = datetime.now()
        duration = end - start
        logger.info("* Validated in %.2f seconds" % duration.seconds)
    else:
        v = { 'validation': 'Not Run' }

    if v['validation'] == "Error count 0\n" or v['validation'].find('Not Run') == 0:   ## yes with CR
    
        logger.info("* Posting file and metadata to ENCODEd...")
        f_obj = encd.post_file(filename, file_meta, SERVER, AUTHID, AUTHPW)
        v['accession'] = f_obj.get('accession', "NOT POSTED")
        if v['accession'] == "NOT POSTED":
            v['accession'] = f_obj.get("external_accession", "NOT POSTED")
        if v['accession'] == "NOT POSTED":
            v['accession'] = file_meta.get("external_accession", "NOT POSTED")
            print "* Returned f_obj..."
            print json.dumps(f_obj, indent=4, sort_keys=True)
            raise # This will ensure that splashdown doesn't continue uploading.
        
        post_status = f_obj.get('status','upload failed')       
        if post_status == 'upload failed':
            logger.info("* Post ERROR on %s to '%s': %s" % (filename,v['accession'],post_status))
            # NOTE: need to set the accession to dx file nonetheless, since the file object was created in encodeD
        else:
            logger.info("* Posted %s to '%s'" % (filename,v['accession']))

        # update pipe_file md5sum and accession properties
        dx.file_set_property(fid,'md5sum',file_meta['md5sum'],proj_id=dxpy.PROJECT_CONTEXT_ID,verbose=True)
        acc_key = dx.property_accesion_key(SERVER)
        if post_status == 'upload failed':
            acc_key = acc_key + ' upload failed'
        acc = dx.file_set_property(fid,acc_key,v['accession'],proj_id=dxpy.PROJECT_CONTEXT_ID,verbose=True)
        if acc == None or acc != v['accession']:
            logger.info("* Failed to update '%s' to '%s' in file properties" % (acc_key,v['accession']))
        else:
            logger.info("* Updated '%s' to '%s' in file properties" % (acc_key,acc))
        #logger.debug(json.dumps(f_obj, indent=4, sort_keys=True))

        if post_status == 'upload failed':
            raise # This will ensure that splashdown doesn't continue uploading.

    else:
        logger.info("* File invalid: %s" % v['validation'])
        v['accession'] = "NOT POSTED"

    return v

dxpy.run()
