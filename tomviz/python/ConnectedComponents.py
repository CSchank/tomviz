def transform_scalars(dataset):
    """This filter thresholds an image input, marking voxels within a
    lower and upper intensity range provided as foreground and the
    remaining as background, then generates a label map from the
    connected components in the foreground.
    """

    try:
        import itk
        import vtk
    except Exception as exc:
        print("Could not import necessary module(s) itk and vtk")
        print(exc)

    #----USER SPECIFIED VARIABLES-----#
    ###LOWERTHRESHOLD### # Specify lower threshold
    ###UPPERTHRESHOLD### # Specify upper threhsold
    background_value = 0

    # Add a try/catch around the ITK portion. ITK exceptions are
    # passed up to the Python layer, so we can at least report what
    # went wrong with the script, e.g,, unsupported image type.
    try:
        # Import the VTK image as an ITK image. No copying should take place.
        itk_input_image_type = itk.Image.UC3
        itk_import = itk.VTKImageToImageFilter[itk_input_image_type].New()
        itk_import.SetInput(dataset)
        itk_import.Update()

        # Get the ITK image
        itk_image = itk_import.GetOutput()

        # Set the output type for the binary threshold filter to
        # unsigned short (US). The maximum number representable by the
        # input pixel type in the connected components filter below
        # determines how many connected components can be extracted
        # from the binary image - if the type's maximum value is less
        # than the extracted components, the filter will throw an
        # exception.
        itk_threshold_image_type = itk.Image.US3

        # Cast the image to unsigned chars. Probably want floats at
        # some point, but this is known to work for this sequence of
        # operations.
        cast_filter = itk.CastImageFilter[itk_input_image_type, itk_threshold_image_type].New()
        cast_filter.SetInput(itk_image)

        # Binary threshold filter
        threshold_filter = itk.BinaryThresholdImageFilter[itk_threshold_image_type, itk_threshold_image_type].New()
        threshold_filter.SetLowerThreshold(lower_threshold)
        threshold_filter.SetUpperThreshold(upper_threshold)
        threshold_filter.SetInput(cast_filter.GetOutput())

        # We'll make the output image type for the connected
        # components filter be the same as that of the threshold
        # output image.
        itk_output_image_type = itk_threshold_image_type

        # ConnectedComponentImageFilter
        connected_filter = itk.ConnectedComponentImageFilter[itk_threshold_image_type,itk_output_image_type].New()
        connected_filter.SetBackgroundValue(background_value)
        connected_filter.SetInput(threshold_filter.GetOutput())

        # Relabel filter. This will compress the label numbers to a
        # continugous range between 1 and n where n is the number of
        # labels. It will also sort the components from largest to
        # smallest, where the largest component has label 1, the
        # second largest has label 2, and so on...
        relabel_filter = itk.RelabelComponentImageFilter[itk_output_image_type, itk_output_image_type].New()
        relabel_filter.SetInput(connected_filter.GetOutput())
        relabel_filter.SortByObjectSizeOn()
        relabel_filter.Update()

        # Export the ITK image to a VTK image. No copying should take place.
        export_filter = itk.ImageToVTKImageFilter[itk_output_image_type].New()
        export_filter.SetInput(relabel_filter.GetOutput())
        export_filter.Update()

        # Get scalars from the temporary image and copy them to the data set
        result_image = export_filter.GetOutput()
        filter_array = result_image.GetPointData().GetArray(0)

        # Make a new instance of the array that will stick around after this
        # filters in this script are garbage collected
        label_map = filter_array.NewInstance()
        label_map.DeepCopy(filter_array) # Should be able to shallow copy?
        label_map.SetName('LabelMap')

        # Set a new point data array in the dataset
        dataset.GetPointData().AddArray(label_map)

    except Exception as exc:
        print("Exception encountered while running ConnectedComponents")
        print(exc)
