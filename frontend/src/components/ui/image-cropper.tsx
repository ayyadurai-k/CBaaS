import React, { useState, useCallback } from 'react';
import ReactCrop, { Crop, centerCrop, makeAspectCrop, PixelCrop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import { Button } from './button';
import { Loader2, Check, X } from 'lucide-react';

interface ImageCropperProps {
  src: string;
  onCropComplete: (croppedImageBlob: Blob) => void;
  onCancel: () => void;
  isUploading?: boolean;
  uploadProgress?: number;
}

export const ImageCropper: React.FC<ImageCropperProps> = ({
  src,
  onCropComplete,
  onCancel,
  isUploading = false,
  uploadProgress = 0,
}) => {
  const [crop, setCrop] = useState<Crop>();
  const [completedCrop, setCompletedCrop] = useState<PixelCrop | null>(null);
  const [imageRef, setImageRef] = useState<HTMLImageElement | null>(null);

  // Handle image load to center the crop
  const onImageLoad = useCallback((e: React.SyntheticEvent<HTMLImageElement>) => {
    const { naturalWidth: width, naturalHeight: height } = e.currentTarget;

    const initialCrop = centerCrop(
      makeAspectCrop(
        {
          unit: '%',
          width: 50,
        },
        1, // Aspect ratio (1:1 for square crop)
        width,
        height
      ),
      width,
      height
    );

    setCrop(initialCrop);
    setImageRef(e.currentTarget as HTMLImageElement);
  }, []);

  // Generate cropped image blob
  const getCroppedImage = useCallback((): Promise<Blob | null> => {
    if (!completedCrop || !imageRef) return Promise.resolve(null);

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return Promise.resolve(null);

    const scaleX = imageRef.naturalWidth / imageRef.width;
    const scaleY = imageRef.naturalHeight / imageRef.height;

    canvas.width = completedCrop.width;
    canvas.height = completedCrop.height;

    ctx.drawImage(
      imageRef,
      completedCrop.x * scaleX,
      completedCrop.y * scaleY,
      completedCrop.width * scaleX,
      completedCrop.height * scaleY,
      0,
      0,
      completedCrop.width,
      completedCrop.height
    );

    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        resolve(blob);
      }, 'image/jpeg', 0.95);
    });
  }, [completedCrop, imageRef]);

  // Handle crop completion
  const handleCrop = useCallback(async () => {
    try {
      const croppedBlob = await getCroppedImage();
      if (croppedBlob) {
        onCropComplete(croppedBlob);
      }
    } catch (error) {
      console.error('Error cropping image:', error);
    }
  }, [getCroppedImage, onCropComplete]);

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-semibold text-slate-900 mb-2">Crop Your Image</h3>
        <p className="text-sm text-slate-600">Adjust the crop area as needed</p>
      </div>

      <div className="flex justify-center">
        <ReactCrop
          crop={crop}
          onChange={(newCrop) => setCrop(newCrop)}
          onComplete={(c) => setCompletedCrop(c)}
          aspect={1} // 1:1 aspect ratio
        >
          <img src={src} alt="Crop preview" onLoad={onImageLoad} />
        </ReactCrop>
      </div>

      {isUploading && (
        <div className="space-y-3">
          <div className="flex items-center justify-center gap-2 text-sm text-slate-600">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Processing image...</span>
          </div>
          <div className="text-center text-xs text-slate-500">{uploadProgress}% complete</div>
        </div>
      )}

      <div className="flex gap-3 justify-end">
        <Button variant="outline" onClick={onCancel} disabled={isUploading} className="px-6">
          <X className="w-4 h-4 mr-2" />
          Cancel
        </Button>
        <Button onClick={handleCrop} disabled={isUploading || !completedCrop} className="px-6">
          {isUploading ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Check className="w-4 h-4 mr-2" />
          )}
          Apply Crop
        </Button>
      </div>
    </div>
  );
};
